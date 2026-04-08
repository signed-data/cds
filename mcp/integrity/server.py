"""
SignedData CDS — MCP Server: Brazil Integrity (sanctions / compliance)
Exposes Portal da Transparência federal sanction registries as MCP tools.

Phase 1 tool surface:
    - check_sanctions_by_cnpj(cnpj): parallel CEIS/CNEP/CEPIM lookup,
      returns one signed consolidated event.

Usage (installed CLI — for Claude Desktop or Claude Code):
    signeddata-mcp-integrity

Usage (source checkout — for local development):
    python server.py

Environment:
    PORTAL_TRANSPARENCIA_TOKEN — required for any real API call.
    CDS_PRIVATE_KEY_PATH       — optional. When set, events are signed.
    CDS_ISSUER                 — optional. Defaults to 'signed-data.org'.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Path setup ─────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "sdk/python"))

import httpx  # noqa: E402
from fastmcp import FastMCP  # noqa: E402

from cds.schema import CDSEvent  # noqa: E402
from cds.signer import CDSSigner  # noqa: E402
from cds.sources.integrity import MissingTokenError, SanctionsFetcher  # noqa: E402

# ── Server config ───────────────────────────────────────────

mcp = FastMCP(
    name="signeddata-integrity",
    instructions=(
        "Returns Brazilian federal sanction status (CEIS, CNEP, CEPIM) "
        "from Portal da Transparência for a given CNPJ. "
        "All data is signed and timestamped by signed-data.org. "
        "Sanction records include public CPF/CNPJ of sanctioned parties as "
        "published by the Controladoria-Geral da União (CGU) under "
        "Lei de Acesso à Informação 12.527/2011."
    ),
)

# ── Signing (optional) ─────────────────────────────────────

_PRIVATE_KEY_PATH = os.environ.get("CDS_PRIVATE_KEY_PATH", "")
_ISSUER = os.environ.get("CDS_ISSUER", "signed-data.org")


def _get_signer() -> CDSSigner | None:
    if _PRIVATE_KEY_PATH and Path(_PRIVATE_KEY_PATH).exists():
        return CDSSigner(_PRIVATE_KEY_PATH, issuer=_ISSUER)
    return None


def _get_token() -> str:
    return os.environ.get("PORTAL_TRANSPARENCIA_TOKEN", "")


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
async def check_sanctions_by_cnpj(cnpj: str) -> dict[str, Any]:
    """
    Check if a Brazilian CNPJ appears in any federal sanction registry.

    Queries CEIS (empresas inidôneas e suspensas), CNEP (Lei Anticorrupção),
    and CEPIM (entidades sem fins lucrativos impedidas) in parallel and
    returns one signed consolidated result.

    This is the primary due-diligence/KYC primitive for the integrity.brazil
    domain. The signature proves that Portal da Transparência returned this
    data at the query timestamp — a cryptographically verifiable audit record
    of "we checked CNPJ X at T and this is what was published".

    Args:
        cnpj: Brazilian CNPJ number (e.g., "33.000.167/0001-01" or "33000167000101").
              CNPJ check digits are validated before any API call.
    """
    try:
        fetcher = SanctionsFetcher(token=_get_token(), signer=_get_signer())
    except MissingTokenError as exc:
        return {
            "error": "missing_token",
            "detail": str(exc),
            "cnpj": cnpj,
        }

    try:
        event = await fetcher.fetch_consolidated(cnpj)
    except ValueError as exc:
        return {
            "error": "invalid_cnpj",
            "detail": str(exc),
            "cnpj": cnpj,
        }
    except httpx.HTTPStatusError as exc:
        return {
            "error": "upstream_error",
            "detail": f"Portal da Transparência returned {exc.response.status_code}",
            "cnpj": cnpj,
        }

    return _event_to_dict(event)


# ═══════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "sse", "http"], default="stdio")
    parser.add_argument("--port", type=int, default=8013)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse", port=args.port)
    elif args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port, path="/mcp", stateless_http=True)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
