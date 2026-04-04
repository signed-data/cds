"""
SignedData CDS — MCP Server: Brazil Finance
Exposes BCB rates, IPCA, FX, B3 stock quotes, and Copom decisions as MCP tools.

Usage (stdio transport — for Claude Desktop or Claude Code):
    python -m mcp.finance.server

Usage (SSE transport — for web clients):
    python -m mcp.finance.server --transport sse --port 8010

Install:
    pip install fastmcp httpx pydantic cryptography
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
from cds.signer import CDSSigner, CDSVerifier
from cds.sources.finance_models import (
    CopomDecision,
    FinanceContentTypes,
    FXRate,
    IPCAIndex,
    SELICRate,
    StockQuote,
)
from cds.sources.finance import (
    BCB_SGS_BASE,
    BRAPI_BASE,
    COPOM_URL,
    SGS_CDI,
    SGS_EUR_BRL,
    SGS_IGPM,
    SGS_IPCA_12M,
    SGS_IPCA_MONTHLY,
    SGS_SELIC,
    SGS_USD_BRL_BUY,
    SGS_USD_BRL_SELL,
    _bcb_url,
    _daily_rate,
    _fingerprint,
    _parse_bcb_date,
)
from cds.vocab import CDSSources

# ── Server config ───────────────────────────────────────────

mcp = FastMCP(
    name="signeddata-finance",
    instructions=(
        "Provides signed, verified Brazilian financial data from the "
        "Banco Central do Brasil (SELIC, CDI, IPCA, IGP-M, PTAX FX rates, "
        "Copom decisions) and Brapi (B3 stock quotes, crypto). "
        "All data is cryptographically signed by signed-data.org. "
        "Always cite the source and date when presenting financial data."
    ),
)

# ── Signing (optional) ─────────────────────────────────────

_PRIVATE_KEY_PATH = os.environ.get("CDS_PRIVATE_KEY_PATH", "")
_ISSUER = os.environ.get("CDS_ISSUER", "signed-data.org")
_PUBLIC_KEY_PATH = os.environ.get("CDS_PUBLIC_KEY_PATH", "")


def _get_signer() -> CDSSigner | None:
    if _PRIVATE_KEY_PATH and Path(_PRIVATE_KEY_PATH).exists():
        return CDSSigner(_PRIVATE_KEY_PATH, issuer=_ISSUER)
    return None


def _get_verifier() -> CDSVerifier | None:
    if _PUBLIC_KEY_PATH and Path(_PUBLIC_KEY_PATH).exists():
        return CDSVerifier(_PUBLIC_KEY_PATH)
    return None


# ── HTTP helpers ────────────────────────────────────────────


async def _fetch_bcb_sgs(series_code: int, last_n: int = 1) -> tuple[list[dict], str]:
    url = _bcb_url(series_code, last_n)
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        fp = _fingerprint(resp.content)
        return resp.json(), fp


async def _fetch_brapi(endpoint: str, params: dict | None = None) -> tuple[dict, str]:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{BRAPI_BASE}/{endpoint}", params=params)
        resp.raise_for_status()
        fp = _fingerprint(resp.content)
        return resp.json(), fp


def _make_event(
    content_type: str,
    source_id: str,
    fp: str,
    occurred_at: datetime,
    payload: dict,
    summary: str,
) -> dict[str, Any]:
    event = CDSEvent(
        content_type=content_type,
        source=SourceMeta(id=source_id, fingerprint=fp),
        occurred_at=occurred_at,
        lang="pt-BR",
        payload=payload,
        event_context=ContextMeta(summary=summary, model="rule-based-v1"),
    )
    signer = _get_signer()
    if signer:
        signer.sign(event)
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
async def get_selic_rate(last_n: int = 1) -> list[dict[str, Any]]:
    """
    Get the current SELIC overnight rate from the Banco Central do Brasil.
    Returns the last N values (default 1). The SELIC rate is updated daily
    on business days and is the benchmark interest rate in Brazil.

    Args:
        last_n: Number of recent values to return (1-30). Defaults to 1.
    """
    last_n = max(1, min(last_n, 30))
    data, fp = await _fetch_bcb_sgs(SGS_SELIC, last_n)
    results = []
    for item in data:
        date_iso = _parse_bcb_date(item["data"])
        annual = float(item["valor"])
        payload = {
            "date": date_iso,
            "rate_annual": annual,
            "rate_daily": round(_daily_rate(annual), 6),
            "unit": "% a.a.",
            "effective_date": date_iso,
        }
        results.append(_make_event(
            FinanceContentTypes.SELIC, CDSSources.BCB_API, fp,
            datetime.fromisoformat(f"{date_iso}T18:30:00-03:00"),
            payload,
            f"SELIC: {annual}% a.a. ({date_iso})",
        ))
    return results


@mcp.tool()
async def get_ipca(last_n: int = 1) -> list[dict[str, Any]]:
    """
    Get the latest IPCA consumer price index from the Banco Central.
    Includes monthly variation and 12-month accumulated inflation.

    Args:
        last_n: Number of recent months to return (1-12). Defaults to 1.
    """
    last_n = max(1, min(last_n, 12))
    monthly_data, fp1 = await _fetch_bcb_sgs(SGS_IPCA_MONTHLY, last_n)
    acc_data, fp2 = await _fetch_bcb_sgs(SGS_IPCA_12M, last_n)
    fp = fp1  # primary fingerprint
    results = []
    for m_item, a_item in zip(monthly_data, acc_data):
        date_iso = _parse_bcb_date(m_item["data"])
        monthly = float(m_item["valor"])
        acc_12m = float(a_item["valor"])
        payload = {
            "date": date_iso,
            "monthly_pct": monthly,
            "accumulated_12m": acc_12m,
            "accumulated_year": 0.0,
            "base_year": 1993,
        }
        results.append(_make_event(
            FinanceContentTypes.IPCA, CDSSources.BCB_API, fp,
            datetime.fromisoformat(f"{date_iso}T12:00:00-03:00"),
            payload,
            f"IPCA {date_iso}: {monthly}% no mês, {acc_12m}% em 12 meses",
        ))
    return results


@mcp.tool()
async def get_igpm(last_n: int = 1) -> list[dict[str, Any]]:
    """
    Get the latest IGP-M general price index from the Banco Central.

    Args:
        last_n: Number of recent months to return (1-12). Defaults to 1.
    """
    last_n = max(1, min(last_n, 12))
    data, fp = await _fetch_bcb_sgs(SGS_IGPM, last_n)
    results = []
    for item in data:
        date_iso = _parse_bcb_date(item["data"])
        monthly = float(item["valor"])
        payload = {"date": date_iso, "monthly_pct": monthly}
        results.append(_make_event(
            FinanceContentTypes.IGPM, CDSSources.BCB_API, fp,
            datetime.fromisoformat(f"{date_iso}T12:00:00-03:00"),
            payload,
            f"IGP-M {date_iso}: {monthly}% no mês",
        ))
    return results


@mcp.tool()
async def get_usd_brl(last_n: int = 1) -> list[dict[str, Any]]:
    """
    Get the PTAX USD/BRL exchange rate from the Banco Central.
    Returns buy and sell rates from the BCB official PTAX bulletin.

    Args:
        last_n: Number of recent days to return (1-30). Defaults to 1.
    """
    last_n = max(1, min(last_n, 30))
    buy_data, fp1 = await _fetch_bcb_sgs(SGS_USD_BRL_BUY, last_n)
    sell_data, _ = await _fetch_bcb_sgs(SGS_USD_BRL_SELL, last_n)
    results = []
    for buy_item, sell_item in zip(buy_data, sell_data):
        date_iso = _parse_bcb_date(buy_item["data"])
        buy_val = float(buy_item["valor"])
        sell_val = float(sell_item["valor"])
        mid = round((buy_val + sell_val) / 2, 4)
        payload = {
            "date": date_iso,
            "buy": buy_val,
            "sell": sell_val,
            "mid": mid,
            "currency_from": "USD",
            "currency_to": "BRL",
            "source": "ptax",
        }
        results.append(_make_event(
            FinanceContentTypes.USD_BRL, CDSSources.BCB_API, fp1,
            datetime.fromisoformat(f"{date_iso}T18:00:00-03:00"),
            payload,
            f"USD/BRL PTAX {date_iso}: compra {buy_val:.4f}, venda {sell_val:.4f}",
        ))
    return results


@mcp.tool()
async def get_fx_rates(last_n: int = 1) -> list[dict[str, Any]]:
    """
    Get multiple FX rates at once: USD/BRL and EUR/BRL from BCB PTAX.

    Args:
        last_n: Number of recent days to return (1-30). Defaults to 1.
    """
    last_n = max(1, min(last_n, 30))
    results = await get_usd_brl(last_n)

    # EUR/BRL
    eur_data, fp = await _fetch_bcb_sgs(SGS_EUR_BRL, last_n)
    for item in eur_data:
        date_iso = _parse_bcb_date(item["data"])
        val = float(item["valor"])
        payload = {
            "date": date_iso,
            "buy": val, "sell": val, "mid": val,
            "currency_from": "EUR", "currency_to": "BRL", "source": "ptax",
        }
        results.append(_make_event(
            FinanceContentTypes.EUR_BRL, CDSSources.BCB_API, fp,
            datetime.fromisoformat(f"{date_iso}T18:00:00-03:00"),
            payload,
            f"EUR/BRL PTAX {date_iso}: {val:.4f}",
        ))
    return results


@mcp.tool()
async def get_stock_quote(tickers: list[str]) -> list[dict[str, Any]]:
    """
    Get real-time B3 stock quotes from Brapi.
    Supports ações, FIIs, BDRs. Up to 10 tickers per request.

    Args:
        tickers: List of B3 ticker symbols (e.g., ["PETR4", "VALE3", "ITUB4"]).
    """
    tickers = tickers[:10]
    ticker_str = ",".join(tickers)
    data, fp = await _fetch_brapi(f"quote/{ticker_str}")
    results = []
    for item in data.get("results", []):
        ticker = item.get("symbol", "")
        price = float(item.get("regularMarketPrice", 0))
        change_pct = float(item.get("regularMarketChangePercent", 0))
        state = item.get("marketState", "CLOSED")

        ct = FinanceContentTypes.STOCK
        if ticker.endswith("11") and len(ticker) == 6:
            ct = FinanceContentTypes.FII

        payload = {
            "ticker": ticker,
            "short_name": item.get("shortName", ""),
            "long_name": item.get("longName", ""),
            "currency": item.get("currency", "BRL"),
            "market_price": price,
            "change": float(item.get("regularMarketChange", 0)),
            "change_pct": change_pct,
            "previous_close": float(item.get("regularMarketPreviousClose", 0)),
            "open": item.get("regularMarketOpen"),
            "day_high": float(item.get("regularMarketDayHigh", 0)),
            "day_low": float(item.get("regularMarketDayLow", 0)),
            "volume": int(item.get("regularMarketVolume", 0)),
            "market_cap": item.get("marketCap"),
            "exchange": item.get("fullExchangeName", "SAO"),
            "market_state": state,
            "timestamp": item.get("regularMarketTime", datetime.now(UTC).isoformat()),
        }
        results.append(_make_event(
            ct, CDSSources.BRAPI, fp,
            datetime.now(UTC),
            payload,
            f"{ticker}: R$ {price:.2f} ({change_pct:+.2f}%) — {state}",
        ))
    return results


@mcp.tool()
async def get_market_summary() -> dict[str, Any]:
    """
    Get a quick market summary: SELIC rate, USD/BRL PTAX, and IBOV index
    in one call. Useful for a daily market overview.
    """
    selic_results = await get_selic_rate(1)
    fx_results = await get_usd_brl(1)

    return {
        "selic": selic_results[0] if selic_results else None,
        "usd_brl": fx_results[0] if fx_results else None,
        "summary": "Market summary with SELIC rate and USD/BRL PTAX.",
    }


@mcp.tool()
async def get_copom_history(last_n: int = 5) -> list[dict[str, Any]]:
    """
    Get the last N Copom monetary policy decisions.
    Includes whether SELIC was raised, cut, or maintained, and by how much.

    Args:
        last_n: Number of recent decisions to return (1-20). Defaults to 5.
    """
    last_n = max(1, min(last_n, 20))
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(COPOM_URL)
        resp.raise_for_status()
        fp = _fingerprint(resp.content)
        data = resp.json()

    results = []
    meetings = data.get("conteudo", [])[:last_n]
    for item in meetings:
        rate_after = float(item.get("metaSelic", 0))
        rate_before = float(item.get("metaSelicAnterior", rate_after))
        diff_bps = round((rate_after - rate_before) * 100)
        decision = "raise" if diff_bps > 0 else "cut" if diff_bps < 0 else "maintain"
        meeting_date = item.get("dataReuniao", "")
        number = int(item.get("numeroReuniao", 0))

        payload = {
            "meeting_number": number,
            "meeting_date": meeting_date,
            "decision": decision,
            "rate_before": rate_before,
            "rate_after": rate_after,
            "rate_change_bps": diff_bps,
            "vote_unanimous": item.get("unanime", True),
            "statement_url": item.get("urlAta"),
        }
        try:
            occurred = datetime.fromisoformat(f"{meeting_date}T18:30:00-03:00")
        except (ValueError, TypeError):
            occurred = datetime.now(UTC)

        results.append(_make_event(
            FinanceContentTypes.COPOM, CDSSources.BCB_API, fp,
            occurred, payload,
            f"Copom #{number}: {decision} SELIC em {rate_after}% a.a.",
        ))
    return results


@mcp.tool()
async def get_copom_latest() -> dict[str, Any]:
    """
    Get the most recent Copom decision. Shortcut for get_copom_history(1).
    """
    results = await get_copom_history(1)
    return results[0] if results else {"error": "No Copom data available"}


# ═══════════════════════════════════════════════════════════
# RESOURCES
# ═══════════════════════════════════════════════════════════


@mcp.resource("finance://selic/latest")
async def selic_latest_resource() -> str:
    """Latest SELIC rate as a signed CDS JSON resource."""
    results = await get_selic_rate(1)
    return json.dumps(results[0] if results else {}, ensure_ascii=False, indent=2)


@mcp.resource("finance://usd-brl/latest")
async def usd_brl_latest_resource() -> str:
    """Latest USD/BRL PTAX rate."""
    results = await get_usd_brl(1)
    return json.dumps(results[0] if results else {}, ensure_ascii=False, indent=2)


@mcp.resource("finance://ipca/latest")
async def ipca_latest_resource() -> str:
    """Latest IPCA index."""
    results = await get_ipca(1)
    return json.dumps(results[0] if results else {}, ensure_ascii=False, indent=2)


@mcp.resource("finance://market-summary")
async def market_summary_resource() -> str:
    """Quick market summary: SELIC + USD/BRL."""
    data = await get_market_summary()
    return json.dumps(data, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--port", type=int, default=8010)
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse", port=args.port)
    else:
        mcp.run(transport="stdio")
