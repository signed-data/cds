"""
SignedData CDS — MCP Server: Brazil Government Transparency (gov-br)
Exposes Brazilian government transparency data from Portal da Transparência as MCP tools.

Phase 1: Sanctions status (CEIS + CNEP) by CNPJ lookup.

Usage (stdio transport — for Claude Desktop or Claude Code):
    python -m mcp.gov_br.server

Usage (HTTP transport — for Lambda Function URL):
    python -m mcp.gov_br.server --transport http --host 0.0.0.0 --port 8080
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ── Path setup ─────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "sdk/python"))

from fastmcp import FastMCP

from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.signer import CDSSigner, CDSVerifier
from cds.sources.gov_br_models import GovBrContentTypes, SanctionsConsolidated
from cds.sources.gov_br import fetch_sanctions
from cds.vocab import CDSSources

# ── Server config ───────────────────────────────────────────
mcp = FastMCP(
    name="signeddata-gov-br",
    instructions=(
        "Returns Brazilian federal transparency data from Portal da Transparência. "
        "Phase 1: CEIS and CNEP sanction status by CNPJ. "
        "All data is signed and timestamped by signed-data.org. "
        "Sanction records are published by Controladoria-Geral da União (CGU)."
    ),
)

# ── Signing (optional) ─────────────────────────────────────
_PRIVATE_KEY_PATH = os.environ.get("CDS_PRIVATE_KEY_PATH", "")
_ISSUER = os.environ.get("CDS_ISSUER", "signed-data.org")
_PORTAL_TOKEN = os.environ.get("PORTAL_TRANSPARENCIA_TOKEN", "")


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
async def check_sanctions(cnpj: str) -> dict[str, Any]:
    """
    Check CNPJ sanction status from CEIS (empresas inidôneas) and CNEP (Lei Anticorrupção).

    Returns consolidated sanctions status:
    - sanction_found: boolean — true if record found in either registry
    - sanction_count: integer — total records (CEIS + CNEP)
    - registries.ceis: array — CEIS suspension/disqualification records
    - registries.cnep: array — CNEP Anti-Corruption Law sanctions
    - is_currently_sanctioned: computed property — true if any active penalty

    Args:
        cnpj: Brazilian CNPJ (e.g., "11.222.333/0001-44" or "11222333000144").
              CNPJ is validated before API call.

    Returns:
        Signed CDS Event wrapping SanctionsConsolidated payload.
    """
    if not _PORTAL_TOKEN:
        raise ValueError("PORTAL_TRANSPARENCIA_TOKEN environment variable not set")

    # Fetch sanctions from Portal da Transparência
    sanctions = await fetch_sanctions(cnpj, _PORTAL_TOKEN)

    # Wrap in CDSEvent and optionally sign
    event = CDSEvent(
        id=f"sanctions-{sanctions.cnpj}-{sanctions.query_timestamp.replace(':', '-').replace('+', '-')}",
        content_type=GovBrContentTypes.SANCTIONS_CONSOLIDATED,
        occurred_at=datetime.now(UTC).isoformat(),
        source=SourceMeta(uri=CDSSources.PORTAL_DA_TRANSPARENCIA),
        payload=sanctions.model_dump(),
        event_context=ContextMeta(
            summary=f"Sanction check: {sanctions.cnpj_formatted} — {sanctions.sanction_count} record(s) found"
        ),
    )

    # Sign if private key available
    signer = _get_signer()
    if signer:
        event = signer.sign(event)

    return _event_to_dict(event)


if __name__ == "__main__":
    # Run with: python -m mcp.gov_br.server
    mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), path="/mcp", stateless_http=True)
