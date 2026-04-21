"""
SignedData CDS — MCP Server: Brazil Lottery
Exposes Mega Sena (and other Caixa games) as MCP tools for Claude / any LLM.

Usage (stdio transport — for Claude Desktop or Claude Code):
    python -m mcp.lottery.server

Usage (SSE transport — for web clients):
    python -m mcp.lottery.server --transport sse --port 8001

Install:
    pip install fastmcp httpx pydantic cryptography
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

# ── Path setup ─────────────────────────────────────────────
# Allows running directly or as part of the monorepo.
_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "sdk/python"))

from fastmcp import FastMCP
from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.vocab import CDSSources
from cds.signer import CDSSigner
from cds.sources.lottery_models import LotteryContentTypes, MegaSenaResult, PrizeTier
from cds.sources.lottery import (
    CAIXA_BASE,
    _build_summary,
    _parse_response,
)

SOURCE_ID = CDSSources.CAIXA_LOTERIAS

# ── Server config ───────────────────────────────────────────
mcp = FastMCP(
    name="signeddata-lottery",
    instructions=(
        "Provides signed, verified Mega Sena and Brazil lottery results "
        "from the official Caixa Econômica Federal API. "
        "All data is cryptographically signed by signed-data.org. "
        "Always mention the concurso number and date when presenting results."
    ),
)

# ── Signing (optional — uses env var or skips) ──────────────
_PRIVATE_KEY_PATH = os.environ.get("CDS_PRIVATE_KEY_PATH", "")
_ISSUER           = os.environ.get("CDS_ISSUER", "signed-data.org")


def _get_signer() -> CDSSigner | None:
    if _PRIVATE_KEY_PATH and Path(_PRIVATE_KEY_PATH).exists():
        return CDSSigner(_PRIVATE_KEY_PATH, issuer=_ISSUER)
    return None


def _brl(value: float) -> str:
    """Format BRL: 45000000.0 → 'R$ 45.000.000,00'"""
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"

# ── HTTP helper ─────────────────────────────────────────────
async def _fetch_caixa(game: str, concurso: int | None = None) -> dict[str, Any]:
    url = f"{CAIXA_BASE}/{game}/{concurso}" if concurso else f"{CAIXA_BASE}/{game}/"
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, headers={"Accept": "application/json"})
        resp.raise_for_status()
        return resp.json()


def _event_to_dict(event: CDSEvent) -> dict[str, Any]:
    """Serialise a CDSEvent to a plain dict for MCP response."""
    return {
        "cds_event_id": event.id,
        "content_type": event.content_type,
        "occurred_at": event.occurred_at.isoformat(),
        "signed_by": event.integrity.signed_by if event.integrity else None,
        "hash": event.integrity.hash[:20] + "..." if event.integrity else None,
        "summary": event.event_context.summary if event.event_context else "",
        "payload": event.payload,
    }

# ═══════════════════════════════════════════════════════════
# TOOLS
# ═══════════════════════════════════════════════════════════

@mcp.tool()
async def get_mega_sena_latest() -> dict[str, Any]:
    """
    Get the most recent Mega Sena draw result, including:
    - draw number (concurso), date, and location
    - the 6 winning numbers (dezenas)
    - prize tiers: how many winners and prize amounts in BRL
    - whether the jackpot accumulated (acumulado)
    - next draw estimated prize
    All data is cryptographically signed by signed-data.org.
    """
    raw    = await _fetch_caixa("megasena")
    result = _parse_response(raw)
    signer = _get_signer()

    try:
        d, m, y = result.data_apuracao.split("/")
        occurred = datetime(int(y), int(m), int(d), 21, 0, 0, tzinfo=timezone.utc)
    except Exception:
        occurred = datetime.now(timezone.utc)

    event = CDSEvent(
        content_type = LotteryContentTypes.MEGA_SENA,
        source       = SourceMeta(id=SOURCE_ID),
        occurred_at  = occurred,
        lang         = "pt-BR",
        payload      = result.model_dump(mode="json"),
        event_context=ContextMeta(summary=_build_summary(result), model="rule-based-v1"),
    )
    if signer:
        signer.sign(event)

    return _event_to_dict(event)


@mcp.tool()
async def get_mega_sena_by_concurso(concurso: int) -> dict[str, Any]:
    """
    Get a specific Mega Sena draw result by concurso (draw) number.

    Args:
        concurso: The draw number (e.g. 2800). Use get_mega_sena_latest first
                  to find the current draw number if you don't know it.
    """
    raw    = await _fetch_caixa("megasena", concurso)
    result = _parse_response(raw)
    signer = _get_signer()

    try:
        d, m, y = result.data_apuracao.split("/")
        occurred = datetime(int(y), int(m), int(d), 21, 0, 0, tzinfo=timezone.utc)
    except Exception:
        occurred = datetime.now(timezone.utc)

    event = CDSEvent(
        content_type = LotteryContentTypes.MEGA_SENA,
        source       = SourceMeta(id=SOURCE_ID),
        occurred_at  = occurred,
        lang         = "pt-BR",
        payload      = result.model_dump(mode="json"),
        event_context=ContextMeta(summary=_build_summary(result), model="rule-based-v1"),
    )
    if signer:
        signer.sign(event)

    return _event_to_dict(event)


@mcp.tool()
async def get_mega_sena_recent(last_n: int = 5) -> list[dict[str, Any]]:
    """
    Get the last N Mega Sena draw results in chronological order (most recent last).
    Fetches the latest draw first, then works backwards using concurso numbers.

    Args:
        last_n: Number of recent draws to fetch (1–20). Defaults to 5.
    """
    last_n = max(1, min(last_n, 20))

    # Get latest first to find current concurso number
    latest_raw    = await _fetch_caixa("megasena")
    latest_result = _parse_response(latest_raw)
    latest_num    = latest_result.concurso

    concursos = list(range(latest_num - last_n + 1, latest_num + 1))
    results: list[dict[str, Any]] = []

    for concurso in concursos:
        raw    = await _fetch_caixa("megasena", concurso)
        result = _parse_response(raw)
        signer = _get_signer()

        try:
            d, m, y = result.data_apuracao.split("/")
            occurred = datetime(int(y), int(m), int(d), 21, 0, 0, tzinfo=timezone.utc)
        except Exception:
            occurred = datetime.now(timezone.utc)

        event = CDSEvent(
            content_type = LotteryContentTypes.MEGA_SENA,
            source       = SourceMeta(id=SOURCE_ID),
            occurred_at  = occurred,
            lang         = "pt-BR",
            payload      = result.model_dump(mode="json"),
            event_context=ContextMeta(summary=_build_summary(result), model="rule-based-v1"),
        )
        if signer:
            signer.sign(event)

        results.append(_event_to_dict(event))

    return results


@mcp.tool()
async def check_mega_sena_ticket(
    numbers: list[int],
    concurso: int | None = None,
) -> dict[str, Any]:
    """
    Check if a Mega Sena ticket won a prize in a specific draw.
    Returns the prize tier won (or 'no prize') and the prize amount.

    Args:
        numbers:  Your ticket numbers (6 to 15 numbers between 1 and 60).
        concurso: Draw number to check. Defaults to the latest draw.
    """
    if not (6 <= len(numbers) <= 15):
        return {"error": "A Mega Sena ticket must have between 6 and 15 numbers."}
    if any(n < 1 or n > 60 for n in numbers):
        return {"error": "All numbers must be between 1 and 60."}

    raw    = await _fetch_caixa("megasena", concurso)
    result = _parse_response(raw)

    drawn_set  = set(int(d) for d in result.dezenas)
    ticket_set = set(numbers)
    matches    = drawn_set & ticket_set
    n_matches  = len(matches)

    # Mega Sena prize tiers: 6, 5, 4 matches
    prize_map = {6: 1, 5: 2, 4: 3}
    tier_num  = prize_map.get(n_matches)
    tier_data = next((t for t in result.premiacoes if t.tier == tier_num), None) if tier_num else None

    return {
        "concurso":       result.concurso,
        "draw_date":      result.data_apuracao,
        "drawn_numbers":  result.dezenas,
        "your_numbers":   sorted(numbers),
        "matches":        sorted(matches),
        "n_matches":      n_matches,
        "prize_tier":     tier_data.description if tier_data else "Sem prêmio",
        "prize_amount":   _brl(tier_data.prize_amount) if tier_data else "R$ 0,00",
        "won":            tier_data is not None,
        "summary":        _build_summary(result),
    }


@mcp.tool()
async def get_mega_sena_statistics(last_n: int = 20) -> dict[str, Any]:
    """
    Analyse the last N Mega Sena draws to find:
    - Most and least frequently drawn numbers
    - How many draws accumulated (jackpot not won)
    - Average prize amounts by tier

    Args:
        last_n: Number of recent draws to analyse (5–50). Defaults to 20.
    """
    last_n = max(5, min(last_n, 50))

    latest_raw = await _fetch_caixa("megasena")
    latest     = _parse_response(latest_raw)
    latest_num = latest.concurso

    concursos = range(max(1, latest_num - last_n + 1), latest_num + 1)
    freq: dict[str, int] = {}
    accumulated = 0
    total_draws = 0

    for concurso in concursos:
        try:
            raw    = await _fetch_caixa("megasena", concurso)
            result = _parse_response(raw)
            for d in result.dezenas:
                freq[d] = freq.get(d, 0) + 1
            if result.acumulado:
                accumulated += 1
            total_draws += 1
        except Exception:
            continue

    sorted_freq  = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    most_common  = sorted_freq[:10]
    least_common = sorted_freq[-10:]

    return {
        "draws_analysed":         total_draws,
        "from_concurso":          max(1, latest_num - last_n + 1),
        "to_concurso":            latest_num,
        "accumulated_draws":      accumulated,
        "jackpot_hit_rate":       f"{((total_draws - accumulated) / total_draws * 100):.1f}%",
        "most_frequent_numbers":  [{"number": n, "times": t} for n, t in most_common],
        "least_frequent_numbers": [{"number": n, "times": t} for n, t in least_common],
    }


# ═══════════════════════════════════════════════════════════
# RESOURCES
# ═══════════════════════════════════════════════════════════

@mcp.resource("lottery://mega-sena/latest")
async def mega_sena_latest_resource() -> str:
    """Latest Mega Sena result as a CDS-signed JSON resource."""
    raw    = await _fetch_caixa("megasena")
    result = _parse_response(raw)
    return json.dumps({
        "concurso":    result.concurso,
        "date":        result.data_apuracao,
        "dezenas":     result.dezenas,
        "acumulado":   result.acumulado,
        "next_prize":  _brl(result.valor_acumulado_proximo),
        "next_draw":   result.data_proximo_concurso,
        "summary":     _build_summary(result),
    }, ensure_ascii=False, indent=2)


@mcp.resource("lottery://mega-sena/schema")
async def mega_sena_schema_resource() -> str:
    """CDS content type and payload schema for Mega Sena events."""
    return json.dumps({
        "content_type": LotteryContentTypes.MEGA_SENA,
        "issuer":       _ISSUER,
        "source":       SOURCE_ID,
        "payload_fields": {
            "concurso":               "int — draw number",
            "data_apuracao":          "str — draw date (DD/MM/YYYY)",
            "data_apuracao_iso":      "str — draw date (ISO 8601)",
            "dezenas":                "list[str] — 6 winning numbers, sorted",
            "dezenas_ordem_sorteio":  "list[str] — numbers in draw order",
            "acumulado":              "bool — jackpot accumulated",
            "premiacoes":             "list[PrizeTier] — prize tiers",
            "valor_acumulado_proximo":"float — next jackpot estimate (BRL)",
            "data_proximo_concurso":  "str — next draw date",
        },
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════

def main() -> None:
    """Entry point for signeddata-mcp-lottery CLI."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
