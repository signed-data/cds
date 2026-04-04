"""
SignedData CDS — Commodities Brazil Ingestors
Sources:
    B3 Futures: https://brapi.dev/api/quote/{tickers}
    CONAB:      https://consultaweb.conab.gov.br/consultas/consultaGrao/listar
    World Bank: https://api.worldbank.org/v2/en/indicator/{code}
"""
from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from cds.ingestor import BaseIngestor
from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.sources.commodities_models import (
    B3_COMMODITY_TICKERS,
    CONAB_COMMODITY_MAP,
    CommodityContentTypes,
    CommodityFutures,
    CommodityIndex,
    CommoditySpot,
    CONABResponseChangedError,
)
from cds.vocab import CDSSources

logger = logging.getLogger(__name__)

BRAPI_BASE = "https://brapi.dev/api"
CONAB_URL = "https://consultaweb.conab.gov.br/consultas/consultaGrao/listar"
WORLDBANK_BASE = "https://api.worldbank.org/v2/en/indicator"


def _fingerprint(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


# ── B3 Futures Ingestor ───────────────────────────────────


class B3FuturesIngestor(BaseIngestor):
    content_type = CommodityContentTypes.FUTURES_SOJA

    def __init__(
        self,
        signer: Any,
        commodities: list[str] | None = None,
    ) -> None:
        super().__init__(signer)
        # Filter to valid tickers
        if commodities:
            self.tickers = [t for t in commodities if t in B3_COMMODITY_TICKERS]
        else:
            self.tickers = list(B3_COMMODITY_TICKERS.keys())

    async def fetch(self) -> list[CDSEvent]:
        events: list[CDSEvent] = []
        ticker_str = ",".join(self.tickers)

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{BRAPI_BASE}/quote/{ticker_str}")
            resp.raise_for_status()
            fp = _fingerprint(resp.content)
            data = resp.json()

        for item in data.get("results", []):
            symbol = item.get("symbol", "")
            if symbol not in B3_COMMODITY_TICKERS:
                continue

            commodity_name, content_type = B3_COMMODITY_TICKERS[symbol]
            price = float(item.get("regularMarketPrice", 0))
            change = float(item.get("regularMarketChange", 0))
            change_pct = float(item.get("regularMarketChangePercent", 0))
            timestamp = item.get("regularMarketTime", datetime.now(UTC).isoformat())

            futures = CommodityFutures(
                commodity=commodity_name,
                ticker=symbol,
                unit="R$/saca",
                contract_month="",  # Brapi doesn't expose contract month directly
                price=price,
                change=change,
                change_pct=change_pct,
                open=float(item.get("regularMarketOpen", 0)),
                day_high=float(item.get("regularMarketDayHigh", 0)),
                day_low=float(item.get("regularMarketDayLow", 0)),
                volume=int(item.get("regularMarketVolume", 0)),
                timestamp=timestamp,
            )

            occurred = datetime.now(UTC)
            try:
                occurred = datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                pass

            events.append(CDSEvent(
                content_type=content_type,
                source=SourceMeta(id=CDSSources.BRAPI, fingerprint=fp),
                occurred_at=occurred,
                lang="pt-BR",
                payload=futures.model_dump(mode="json"),
                event_context=ContextMeta(
                    summary=(
                        f"{commodity_name.capitalize()} B3 ({symbol}): "
                        f"R$ {price:.2f} ({change_pct:+.2f}%)"
                    ),
                    model="rule-based-v1",
                ),
            ))

        return events


# ── CONAB Spot Ingestor ───────────────────────────────────


def _parse_conab_response(raw: Any) -> list[dict[str, Any]]:
    """
    Parse CONAB response defensively.
    Raises CONABResponseChangedError if the structure is unexpected.
    """
    if not isinstance(raw, list):
        raise CONABResponseChangedError(
            f"Expected list, got {type(raw).__name__}"
        )
    if len(raw) == 0:
        return []

    # Validate expected fields in first item
    first = raw[0]
    required_keys = {"produto", "uf", "preco"}
    if not isinstance(first, dict):
        raise CONABResponseChangedError(
            f"Expected dict items, got {type(first).__name__}"
        )
    missing = required_keys - set(first.keys())
    if missing:
        raise CONABResponseChangedError(
            f"Missing expected keys: {missing}"
        )

    return raw


class CONABSpotIngestor(BaseIngestor):
    content_type = CommodityContentTypes.SPOT_SOJA

    def __init__(
        self,
        signer: Any,
        states: list[str] | None = None,
    ) -> None:
        super().__init__(signer)
        self.states = states  # Filter by UF, e.g. ["MT", "GO"]

    async def fetch(self) -> list[CDSEvent]:
        events: list[CDSEvent] = []

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(CONAB_URL)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                logger.error("CONAB API unreachable: %s", e)
                return []

            fp = _fingerprint(resp.content)

            try:
                raw_data = _parse_conab_response(resp.json())
            except CONABResponseChangedError as e:
                logger.error(
                    "CONAB API response structure changed — skip this cycle: %s", e
                )
                return []

        now = datetime.now(UTC)
        for item in raw_data:
            commodity = str(item.get("produto", "")).lower().strip()
            state = str(item.get("uf", "")).upper().strip()
            price = item.get("preco")

            # Filter by state if requested
            if self.states and state not in self.states:
                continue

            # Map to content type
            content_type = CONAB_COMMODITY_MAP.get(commodity)
            if not content_type:
                continue

            try:
                price_val = float(price)
            except (TypeError, ValueError):
                continue

            spot = CommoditySpot(
                commodity=commodity,
                state=state,
                city=item.get("cidade"),
                unit="R$/60kg",
                price=price_val,
                week=now.strftime("%G-W%V"),
                date_from=now.strftime("%Y-%m-%d"),
                date_to=now.strftime("%Y-%m-%d"),
                conab_notes=item.get("observacao"),
            )

            events.append(CDSEvent(
                content_type=content_type,
                source=SourceMeta(id=CDSSources.CONAB, fingerprint=fp),
                occurred_at=now,
                lang="pt-BR",
                payload=spot.model_dump(mode="json"),
                event_context=ContextMeta(
                    summary=(
                        f"{commodity.capitalize()} {state}: "
                        f"R$ {price_val:.2f}/60kg (CONAB)"
                    ),
                    model="rule-based-v1",
                ),
            ))

        return events


# ── World Bank Index Ingestor ─────────────────────────────


WORLDBANK_INDICATORS = {
    "PSOYBEANS": "Soybeans",
    "PMAIZMT": "Corn (maize)",
    "PCOFFOTM": "Coffee arabica",
}


class WorldBankIndexIngestor(BaseIngestor):
    content_type = CommodityContentTypes.INDEX_WORLDBANK

    def __init__(self, signer: Any) -> None:
        super().__init__(signer)

    async def fetch(self) -> list[CDSEvent]:
        events: list[CDSEvent] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for indicator, name in WORLDBANK_INDICATORS.items():
                url = (
                    f"{WORLDBANK_BASE}/{indicator}"
                    "?date=2025:2026&format=json&per_page=1"
                )
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                except httpx.HTTPError:
                    continue

                fp = _fingerprint(resp.content)
                data = resp.json()

                # World Bank returns [metadata, [values]]
                if not isinstance(data, list) or len(data) < 2:
                    continue
                values = data[1]
                if not values:
                    continue

                latest = values[0]
                value = latest.get("value")
                date = latest.get("date", "")

                if value is None:
                    continue

                idx = CommodityIndex(
                    indicator=indicator,
                    name=name,
                    date=date,
                    value=float(value),
                    unit="USD/mt",
                )

                events.append(CDSEvent(
                    content_type=CommodityContentTypes.INDEX_WORLDBANK,
                    source=SourceMeta(id=CDSSources.WORLDBANK, fingerprint=fp),
                    occurred_at=datetime.now(UTC),
                    lang="en",
                    payload=idx.model_dump(mode="json"),
                    event_context=ContextMeta(
                        summary=f"{name} ({indicator}): ${value:.2f}/mt ({date})",
                        model="rule-based-v1",
                    ),
                ))

        return events
