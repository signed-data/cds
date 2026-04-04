"""
SignedData CDS — MCP Server: Brazil Companies (CNPJ)
Exposes company registration data from BrasilAPI / Receita Federal as MCP tools.

Usage (stdio transport — for Claude Desktop or Claude Code):
    python -m mcp.companies.server

Usage (SSE transport — for web clients):
    python -m mcp.companies.server --transport sse --port 8012
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

# ── Path setup ─────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "sdk/python"))

from fastmcp import FastMCP

from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.signer import CDSSigner, CDSVerifier
from cds.sources.companies_models import CompaniesContentTypes
from cds.sources.companies import (
    CNPJFetcher,
    validate_cnpj,
    _format_cnpj,
    _fingerprint,
    BRASILAPI_CNPJ_BASE,
    BRASILAPI_CNAE_BASE,
)
from cds.vocab import CDSSources

# ── Server config ───────────────────────────────────────────

mcp = FastMCP(
    name="signeddata-companies",
    instructions=(
        "Returns public company registration data from the Brazilian Receita Federal "
        "via BrasilAPI. Partner data (QSA) includes public records only. "
        "All data is signed and timestamped by signed-data.org. "
        "CNPJ validation is performed before any API call."
    ),
)

# ── Signing (optional) ─────────────────────────────────────

_PRIVATE_KEY_PATH = os.environ.get("CDS_PRIVATE_KEY_PATH", "")
_ISSUER = os.environ.get("CDS_ISSUER", "signed-data.org")


def _get_signer() -> CDSSigner | None:
    if _PRIVATE_KEY_PATH and Path(_PRIVATE_KEY_PATH).exists():
        return CDSSigner(_PRIVATE_KEY_PATH, issuer=_ISSUER)
    return None


def _event_to_dict(event: CDSEvent) -> dict[str, Any]:
    return {
        "cds_event_id": event.id,
        "content_type": event.content_type,
        "occurred_at": event.occurred_at.isoformat() if isinstance(event.occurred_at, datetime) else event.occurred_at,
        "signed_by": event.integrity.signed_by if event.integrity else None,
        "hash": event.integrity.hash[:20] + "..." if event.integrity else None,
        "summary": event.event_context.summary if event.event_context else "",
        "payload": event.payload,
    }


# ═══════════════════════════════════════════════════════════
# TOOLS
# ═══════════════════════════════════════════════════════════


@mcp.tool()
async def get_company_profile(cnpj: str) -> dict[str, Any]:
    """
    Get the full company profile for a Brazilian CNPJ.
    Returns razão social, situação cadastral, CNAE, endereço, capital social,
    and more. CNPJ is validated before the API call.

    Args:
        cnpj: Brazilian CNPJ number (e.g., "33.000.167/0001-01" or "33000167000101").
    """
    fetcher = CNPJFetcher(signer=_get_signer())
    event = await fetcher.fetch_profile(cnpj)
    return _event_to_dict(event)


@mcp.tool()
async def get_company_partners(cnpj: str) -> dict[str, Any]:
    """
    Get the partner/shareholder data (QSA — quadro societário) for a CNPJ.
    Returns partner names, qualifications, and entry dates.

    Args:
        cnpj: Brazilian CNPJ number.
    """
    fetcher = CNPJFetcher(signer=_get_signer())
    event = await fetcher.fetch_partners(cnpj)
    return _event_to_dict(event)


@mcp.tool()
async def check_company_status(cnpj: str) -> dict[str, Any]:
    """
    Quick check of a company's registration status (ATIVA, BAIXADA, etc.).
    Lighter response than get_company_profile — returns just the essentials.

    Args:
        cnpj: Brazilian CNPJ number.
    """
    fetcher = CNPJFetcher(signer=_get_signer())
    event = await fetcher.fetch_profile(cnpj)
    payload = event.payload
    return {
        "cnpj": payload["cnpj_formatted"],
        "company_name": payload["company_name"],
        "trade_name": payload.get("trade_name"),
        "status": payload["registration_status"],
        "is_active": payload["registration_status"] == "ATIVA",
        "signed_by": event.integrity.signed_by if event.integrity else None,
    }


@mcp.tool()
async def validate_cnpj_tool(cnpj: str) -> dict[str, Any]:
    """
    Validate a CNPJ number without making any API call.
    Returns whether the check digits are valid and the formatted CNPJ.

    Args:
        cnpj: CNPJ to validate (formatted or bare digits).
    """
    try:
        bare = validate_cnpj(cnpj)
        return {
            "valid": True,
            "cnpj_bare": bare,
            "cnpj_formatted": _format_cnpj(bare),
        }
    except ValueError as e:
        return {
            "valid": False,
            "error": str(e),
        }


@mcp.tool()
async def get_cnae_info(code: str) -> dict[str, Any]:
    """
    Get information about a CNAE (economic activity) code.
    Returns the activity description and sector classification.

    Args:
        code: CNAE code (e.g., "0610600").
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{BRASILAPI_CNAE_BASE}/{code}")
        resp.raise_for_status()
        fp = _fingerprint(resp.content)
        data = resp.json()

    event = CDSEvent(
        content_type=CompaniesContentTypes.CNAE,
        source=SourceMeta(id=CDSSources.BRASILAPI, fingerprint=fp),
        occurred_at=datetime.now(UTC),
        lang="pt-BR",
        payload={
            "code": code,
            "description": data.get("descricao", ""),
            "section": data.get("secao", {}).get("descricao", ""),
            "division": data.get("divisao", {}).get("descricao", ""),
            "group": data.get("grupo", {}).get("descricao", ""),
        },
        event_context=ContextMeta(
            summary=f"CNAE {code}: {data.get('descricao', '')}",
            model="rule-based-v1",
        ),
    )
    signer = _get_signer()
    if signer:
        signer.sign(event)
    return _event_to_dict(event)


@mcp.tool()
async def batch_company_lookup(cnpjs: list[str]) -> list[dict[str, Any]]:
    """
    Look up multiple companies at once (up to 10 CNPJs).
    Returns a list of company profiles. Invalid CNPJs are skipped with an error entry.

    Args:
        cnpjs: List of CNPJ numbers (up to 10).
    """
    cnpjs = cnpjs[:10]
    fetcher = CNPJFetcher(signer=_get_signer())
    results = []

    for cnpj in cnpjs:
        try:
            event = await fetcher.fetch_profile(cnpj)
            results.append(_event_to_dict(event))
        except ValueError as e:
            results.append({"cnpj": cnpj, "error": str(e)})
        except httpx.HTTPStatusError as e:
            results.append({"cnpj": cnpj, "error": f"API error: {e.response.status_code}"})

    return results


# ═══════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--port", type=int, default=8012)
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse", port=args.port)
    else:
        mcp.run(transport="stdio")
