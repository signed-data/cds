"""
SignedData CDS — MCP Server: Brazil Commodities
Exposes B3 agro futures, CONAB physical prices, and World Bank indices as MCP tools.

Usage (stdio transport — for Claude Desktop or Claude Code):
    python -m mcp.commodities.server

Usage (SSE transport — for web clients):
    python -m mcp.commodities.server --transport sse --port 8011
"""
from __future__ import annotations

import hashlib
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
from cds.signer import CDSSigner
from cds.sources.commodities_models import (
    B3_COMMODITY_TICKERS,
    CONAB_COMMODITY_MAP,
    CommodityContentTypes,
)
from cds.sources.commodities import (
    B3FuturesIngestor,
    CONABSpotIngestor,
    BRAPI_BASE,
    CONAB_URL,
    _fingerprint,
)
from cds.vocab import CDSSources

# ── Server config ───────────────────────────────────────────

mcp = FastMCP(
    name="signeddata-commodities",
    instructions=(
        "Provides signed Brazilian commodity data: B3 agro futures "
        "(soja, milho, boi gordo, café, açúcar, etanol) and CONAB physical "
        "crop prices. All data is cryptographically signed by signed-data.org. "
        "CONAB data is weekly; B3 futures are near-real-time."
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
async def get_soja_futures() -> dict[str, Any]:
    """
    Get the latest soybean (soja) B3 futures contract quote.
    Returns price, change, volume, and contract details.
    """
    signer = _get_signer()
    ingestor = B3FuturesIngestor(signer or object(), commodities=["SFI"])
    events = await ingestor.fetch()
    if signer:
        events = [signer.sign(e) for e in events]
    return _event_to_dict(events[0]) if events else {"error": "No soja futures data"}


@mcp.tool()
async def get_all_agro_futures() -> list[dict[str, Any]]:
    """
    Get all 6 B3 agricultural commodity futures:
    soja (SFI), milho (CCM), boi gordo (BGI), café (ICF),
    açúcar (SWV), etanol (ETN).
    """
    signer = _get_signer()
    ingestor = B3FuturesIngestor(signer or object())
    events = await ingestor.fetch()
    if signer:
        events = [signer.sign(e) for e in events]
    return [_event_to_dict(e) for e in events]


@mcp.tool()
async def get_futures_by_commodity(ticker: str) -> dict[str, Any]:
    """
    Get a single commodity futures quote by B3 ticker.

    Args:
        ticker: B3 ticker symbol (SFI=soja, CCM=milho, BGI=boi gordo,
                ICF=café, SWV=açúcar, ETN=etanol).
    """
    ticker = ticker.upper()
    if ticker not in B3_COMMODITY_TICKERS:
        return {"error": f"Unknown ticker {ticker}. Valid: {list(B3_COMMODITY_TICKERS.keys())}"}

    signer = _get_signer()
    ingestor = B3FuturesIngestor(signer or object(), commodities=[ticker])
    events = await ingestor.fetch()
    if signer:
        events = [signer.sign(e) for e in events]
    return _event_to_dict(events[0]) if events else {"error": f"No data for {ticker}"}


@mcp.tool()
async def get_soja_spot_prices(states: list[str] | None = None) -> list[dict[str, Any]]:
    """
    Get physical soybean (soja) prices from CONAB by state.

    Args:
        states: Optional list of UF codes to filter (e.g., ["MT", "GO"]).
                Returns all states if omitted.
    """
    signer = _get_signer()
    ingestor = CONABSpotIngestor(signer or object(), states=states)
    events = await ingestor.fetch()
    if signer:
        events = [signer.sign(e) for e in events]
    # Filter to soja only
    soja_events = [e for e in events if e.payload.get("commodity") == "soja"]
    return [_event_to_dict(e) for e in soja_events]


@mcp.tool()
async def get_spot_by_commodity(
    commodity: str,
    states: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Get physical prices for a specific commodity from CONAB.

    Args:
        commodity: One of: soja, milho, trigo, algodao.
        states: Optional list of UF codes to filter.
    """
    commodity = commodity.lower().strip()
    if commodity not in CONAB_COMMODITY_MAP:
        return [{"error": f"Unknown commodity {commodity}. Valid: {list(CONAB_COMMODITY_MAP.keys())}"}]

    signer = _get_signer()
    ingestor = CONABSpotIngestor(signer or object(), states=states)
    events = await ingestor.fetch()
    if signer:
        events = [signer.sign(e) for e in events]
    filtered = [e for e in events if e.payload.get("commodity") == commodity]
    return [_event_to_dict(e) for e in filtered]


@mcp.tool()
async def get_commodity_summary(commodity: str = "soja") -> dict[str, Any]:
    """
    Get futures and spot prices side by side for a commodity.
    Shows the B3 futures price next to the CONAB physical price.

    Args:
        commodity: Commodity name (default: soja).
    """
    # Map commodity name to B3 ticker
    ticker_map = {
        "soja": "SFI",
        "milho": "CCM",
        "café": "ICF",
        "cafe": "ICF",
    }
    ticker = ticker_map.get(commodity.lower())

    futures_data = None
    if ticker:
        result = await get_futures_by_commodity(ticker)
        if "error" not in result:
            futures_data = result

    spot_data = await get_spot_by_commodity(commodity)

    return {
        "commodity": commodity,
        "futures": futures_data,
        "spot_prices": spot_data if isinstance(spot_data, list) else [],
        "summary": f"Commodity summary for {commodity}: futures + spot comparison.",
    }


@mcp.tool()
async def get_basis(
    commodity: str = "soja",
    state: str = "MT",
) -> dict[str, Any]:
    """
    Compute the basis spread: spot price minus futures price.
    This is arithmetic on two signed CDS values — not LLM inference.

    Args:
        commodity: Commodity name (default: soja).
        state: UF code for spot price (default: MT).
    """
    ticker_map = {"soja": "SFI", "milho": "CCM"}
    ticker = ticker_map.get(commodity.lower())
    if not ticker:
        return {"error": f"Basis computation only available for: {list(ticker_map.keys())}"}

    # Get futures
    signer = _get_signer()
    futures_ingestor = B3FuturesIngestor(signer or object(), commodities=[ticker])
    futures_events = await futures_ingestor.fetch()

    # Get spot
    spot_ingestor = CONABSpotIngestor(signer or object(), states=[state])
    spot_events = await spot_ingestor.fetch()
    spot_events = [e for e in spot_events if e.payload.get("commodity") == commodity.lower()]

    if not futures_events or not spot_events:
        return {"error": "Could not fetch both futures and spot prices for basis computation"}

    futures_price = futures_events[0].payload.get("price", 0)
    spot_price = spot_events[0].payload.get("price", 0)
    basis = round(spot_price - futures_price, 2)

    return {
        "basis": basis,
        "basis_unit": "R$/saca",
        "futures_price": futures_price,
        "spot_price": spot_price,
        "futures_source": futures_events[0].id,
        "spot_source": spot_events[0].id,
        "commodity": commodity,
        "state": state,
        "computed": True,
        "llm_generated": False,
    }


# ═══════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--port", type=int, default=8011)
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse", port=args.port)
    else:
        mcp.run(transport="stdio")
