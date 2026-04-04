"""
SignedData CDS — Finance Brazil Ingestors
Sources:
    BCB SGS API: https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados/ultimos/{n}
    Brapi:       https://brapi.dev/api/quote/{tickers}
    Copom:       https://www.bcb.gov.br/api/servico/sitebcb/reunioes-copom/listar
"""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

import httpx

from cds.ingestor import BaseIngestor
from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.sources.finance_models import (
    CDIRate,
    CopomDecision,
    FinanceContentTypes,
    FXRate,
    IGPMIndex,
    IPCAIndex,
    SELICRate,
    StockQuote,
)
from cds.vocab import CDSSources

BCB_SGS_BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados/ultimos/{n}"
BRAPI_BASE = "https://brapi.dev/api"
COPOM_URL = "https://www.bcb.gov.br/api/servico/sitebcb/reunioes-copom/listar"

# BCB SGS series codes
SGS_SELIC = 11
SGS_CDI = 4391
SGS_IPCA_MONTHLY = 433
SGS_IPCA_12M = 432
SGS_IGPM = 189
SGS_USD_BRL_BUY = 1
SGS_USD_BRL_SELL = 2
SGS_EUR_BRL = 21619


def _bcb_url(series_code: int, last_n: int = 1) -> str:
    return BCB_SGS_BASE.format(code=series_code, n=last_n)


def _parse_bcb_date(raw: str) -> str:
    """Convert BCB date 'DD/MM/YYYY' → 'YYYY-MM-DD'."""
    parts = raw.split("/")
    if len(parts) == 3:
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return raw


def _daily_rate(annual_pct: float) -> float:
    """Convert annual rate (%) to daily rate using 252 business days."""
    return ((1 + annual_pct / 100) ** (1 / 252) - 1) * 100


def _fingerprint(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


# ── BCB Rates Ingestor ────────────────────────────────────


class BCBRatesIngestor(BaseIngestor):
    content_type = FinanceContentTypes.SELIC

    def __init__(self, signer: Any, last_n: int = 1) -> None:
        super().__init__(signer)
        self.last_n = last_n

    async def fetch(self) -> list[CDSEvent]:
        events: list[CDSEvent] = []
        async with httpx.AsyncClient(timeout=15) as client:
            # SELIC
            resp = await client.get(_bcb_url(SGS_SELIC, self.last_n))
            resp.raise_for_status()
            fp = _fingerprint(resp.content)
            for item in resp.json():
                date_iso = _parse_bcb_date(item["data"])
                annual = float(item["valor"])
                rate = SELICRate(
                    date=date_iso,
                    rate_annual=annual,
                    rate_daily=round(_daily_rate(annual), 6),
                    effective_date=date_iso,
                )
                events.append(CDSEvent(
                    content_type=FinanceContentTypes.SELIC,
                    source=SourceMeta(id=CDSSources.BCB_API, fingerprint=fp),
                    occurred_at=datetime.fromisoformat(f"{date_iso}T18:30:00-03:00"),
                    lang="pt-BR",
                    payload=rate.model_dump(mode="json"),
                    event_context=ContextMeta(
                        summary=f"SELIC: {rate.rate_annual}% a.a. ({rate.date})",
                        model="rule-based-v1",
                    ),
                ))

            # CDI
            resp = await client.get(_bcb_url(SGS_CDI, self.last_n))
            resp.raise_for_status()
            fp = _fingerprint(resp.content)
            for item in resp.json():
                date_iso = _parse_bcb_date(item["data"])
                annual = float(item["valor"])
                cdi = CDIRate(
                    date=date_iso,
                    rate_annual=annual,
                    rate_daily=round(_daily_rate(annual), 6),
                )
                events.append(CDSEvent(
                    content_type=FinanceContentTypes.CDI,
                    source=SourceMeta(id=CDSSources.BCB_API, fingerprint=fp),
                    occurred_at=datetime.fromisoformat(f"{date_iso}T18:30:00-03:00"),
                    lang="pt-BR",
                    payload=cdi.model_dump(mode="json"),
                    event_context=ContextMeta(
                        summary=f"CDI: {cdi.rate_annual}% a.a. ({cdi.date})",
                        model="rule-based-v1",
                    ),
                ))

        return events


# ── BCB Indices Ingestor ──────────────────────────────────


class BCBIndicesIngestor(BaseIngestor):
    content_type = FinanceContentTypes.IPCA

    def __init__(self, signer: Any, last_n: int = 1) -> None:
        super().__init__(signer)
        self.last_n = last_n

    async def fetch(self) -> list[CDSEvent]:
        events: list[CDSEvent] = []
        async with httpx.AsyncClient(timeout=15) as client:
            # IPCA monthly
            resp_m = await client.get(_bcb_url(SGS_IPCA_MONTHLY, self.last_n))
            resp_m.raise_for_status()
            # IPCA 12-month
            resp_12 = await client.get(_bcb_url(SGS_IPCA_12M, self.last_n))
            resp_12.raise_for_status()
            fp = _fingerprint(resp_m.content + resp_12.content)

            monthly_data = resp_m.json()
            acc_12m_data = resp_12.json()

            for m_item, a_item in zip(monthly_data, acc_12m_data):
                date_iso = _parse_bcb_date(m_item["data"])
                ipca = IPCAIndex(
                    date=date_iso,
                    monthly_pct=float(m_item["valor"]),
                    accumulated_12m=float(a_item["valor"]),
                    accumulated_year=0.0,  # requires additional calculation
                )
                events.append(CDSEvent(
                    content_type=FinanceContentTypes.IPCA,
                    source=SourceMeta(id=CDSSources.BCB_API, fingerprint=fp),
                    occurred_at=datetime.fromisoformat(f"{date_iso}T12:00:00-03:00"),
                    lang="pt-BR",
                    payload=ipca.model_dump(mode="json"),
                    event_context=ContextMeta(
                        summary=(
                            f"IPCA {date_iso}: {ipca.monthly_pct}% no mês, "
                            f"{ipca.accumulated_12m}% em 12 meses"
                        ),
                        model="rule-based-v1",
                    ),
                ))

            # IGP-M
            resp = await client.get(_bcb_url(SGS_IGPM, self.last_n))
            resp.raise_for_status()
            fp = _fingerprint(resp.content)
            for item in resp.json():
                date_iso = _parse_bcb_date(item["data"])
                igpm = IGPMIndex(
                    date=date_iso,
                    monthly_pct=float(item["valor"]),
                )
                events.append(CDSEvent(
                    content_type=FinanceContentTypes.IGPM,
                    source=SourceMeta(id=CDSSources.BCB_API, fingerprint=fp),
                    occurred_at=datetime.fromisoformat(f"{date_iso}T12:00:00-03:00"),
                    lang="pt-BR",
                    payload=igpm.model_dump(mode="json"),
                    event_context=ContextMeta(
                        summary=f"IGP-M {date_iso}: {igpm.monthly_pct}% no mês",
                        model="rule-based-v1",
                    ),
                ))

        return events


# ── BCB FX Ingestor ───────────────────────────────────────


class BCBFXIngestor(BaseIngestor):
    content_type = FinanceContentTypes.USD_BRL

    def __init__(self, signer: Any, last_n: int = 1) -> None:
        super().__init__(signer)
        self.last_n = last_n

    async def fetch(self) -> list[CDSEvent]:
        events: list[CDSEvent] = []
        async with httpx.AsyncClient(timeout=15) as client:
            # USD/BRL buy + sell
            resp_buy = await client.get(_bcb_url(SGS_USD_BRL_BUY, self.last_n))
            resp_buy.raise_for_status()
            resp_sell = await client.get(_bcb_url(SGS_USD_BRL_SELL, self.last_n))
            resp_sell.raise_for_status()
            fp = _fingerprint(resp_buy.content + resp_sell.content)

            for buy_item, sell_item in zip(resp_buy.json(), resp_sell.json()):
                date_iso = _parse_bcb_date(buy_item["data"])
                buy_val = float(buy_item["valor"])
                sell_val = float(sell_item["valor"])
                fx = FXRate(
                    date=date_iso,
                    buy=buy_val,
                    sell=sell_val,
                    mid=round((buy_val + sell_val) / 2, 4),
                    currency_from="USD",
                    currency_to="BRL",
                )
                events.append(CDSEvent(
                    content_type=FinanceContentTypes.USD_BRL,
                    source=SourceMeta(id=CDSSources.BCB_API, fingerprint=fp),
                    occurred_at=datetime.fromisoformat(f"{date_iso}T18:00:00-03:00"),
                    lang="pt-BR",
                    payload=fx.model_dump(mode="json"),
                    event_context=ContextMeta(
                        summary=(
                            f"USD/BRL PTAX {date_iso}: "
                            f"compra {fx.buy:.4f}, venda {fx.sell:.4f}"
                        ),
                        model="rule-based-v1",
                    ),
                ))

            # EUR/BRL
            resp = await client.get(_bcb_url(SGS_EUR_BRL, self.last_n))
            resp.raise_for_status()
            fp = _fingerprint(resp.content)
            for item in resp.json():
                date_iso = _parse_bcb_date(item["data"])
                val = float(item["valor"])
                fx = FXRate(
                    date=date_iso,
                    buy=val,
                    sell=val,
                    mid=val,
                    currency_from="EUR",
                    currency_to="BRL",
                )
                events.append(CDSEvent(
                    content_type=FinanceContentTypes.EUR_BRL,
                    source=SourceMeta(id=CDSSources.BCB_API, fingerprint=fp),
                    occurred_at=datetime.fromisoformat(f"{date_iso}T18:00:00-03:00"),
                    lang="pt-BR",
                    payload=fx.model_dump(mode="json"),
                    event_context=ContextMeta(
                        summary=f"EUR/BRL PTAX {date_iso}: {fx.mid:.4f}",
                        model="rule-based-v1",
                    ),
                ))

        return events


# ── Brapi Quotes Ingestor ─────────────────────────────────


class BrapiQuotesIngestor(BaseIngestor):
    content_type = FinanceContentTypes.STOCK

    def __init__(self, signer: Any, tickers: list[str] | None = None) -> None:
        super().__init__(signer)
        self.tickers = tickers or ["PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3"]

    async def fetch(self) -> list[CDSEvent]:
        events: list[CDSEvent] = []
        ticker_str = ",".join(self.tickers)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{BRAPI_BASE}/quote/{ticker_str}")
            resp.raise_for_status()
            fp = _fingerprint(resp.content)
            data = resp.json()

            for item in data.get("results", []):
                quote = StockQuote(
                    ticker=item.get("symbol", ""),
                    short_name=item.get("shortName", ""),
                    long_name=item.get("longName", ""),
                    currency=item.get("currency", "BRL"),
                    market_price=float(item.get("regularMarketPrice", 0)),
                    change=float(item.get("regularMarketChange", 0)),
                    change_pct=float(item.get("regularMarketChangePercent", 0)),
                    previous_close=float(item.get("regularMarketPreviousClose", 0)),
                    open=item.get("regularMarketOpen"),
                    day_high=float(item.get("regularMarketDayHigh", 0)),
                    day_low=float(item.get("regularMarketDayLow", 0)),
                    volume=int(item.get("regularMarketVolume", 0)),
                    market_cap=item.get("marketCap"),
                    exchange=item.get("fullExchangeName", "SAO"),
                    market_state=item.get("marketState", "CLOSED"),
                    timestamp=item.get("regularMarketTime", datetime.now(UTC).isoformat()),
                )

                # Determine content type: FII tickers end with "11" and have specific patterns
                ct = FinanceContentTypes.STOCK
                if quote.ticker.endswith("11") and len(quote.ticker) == 6:
                    ct = FinanceContentTypes.FII

                occurred = datetime.now(UTC)
                try:
                    occurred = datetime.fromisoformat(quote.timestamp)
                except (ValueError, TypeError):
                    pass

                events.append(CDSEvent(
                    content_type=ct,
                    source=SourceMeta(id=CDSSources.BRAPI, fingerprint=fp),
                    occurred_at=occurred,
                    lang="pt-BR",
                    payload=quote.model_dump(mode="json"),
                    event_context=ContextMeta(
                        summary=(
                            f"{quote.ticker}: R$ {quote.market_price:.2f} "
                            f"({quote.change_pct:+.2f}%) — {quote.market_state}"
                        ),
                        model="rule-based-v1",
                    ),
                ))

        return events


# ── Brapi Crypto Ingestor ─────────────────────────────────


class BrapiCryptoIngestor(BaseIngestor):
    content_type = FinanceContentTypes.CRYPTO

    def __init__(self, signer: Any, coins: list[str] | None = None) -> None:
        super().__init__(signer)
        self.coins = coins or ["BTC", "ETH"]

    async def fetch(self) -> list[CDSEvent]:
        events: list[CDSEvent] = []
        coin_str = ",".join(self.coins)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{BRAPI_BASE}/v2/crypto",
                params={"coin": coin_str, "currency": "BRL"},
            )
            resp.raise_for_status()
            fp = _fingerprint(resp.content)
            data = resp.json()

            for item in data.get("coins", []):
                payload = {
                    "coin": item.get("coin", ""),
                    "name": item.get("coinName", ""),
                    "currency": "BRL",
                    "price": float(item.get("regularMarketPrice", 0)),
                    "change_pct": float(item.get("regularMarketChangePercent", 0)),
                    "market_cap": item.get("marketCap"),
                    "volume_24h": item.get("regularMarketVolume"),
                    "timestamp": item.get("regularMarketTime", ""),
                }
                events.append(CDSEvent(
                    content_type=FinanceContentTypes.CRYPTO,
                    source=SourceMeta(id=CDSSources.BRAPI, fingerprint=fp),
                    occurred_at=datetime.now(UTC),
                    lang="pt-BR",
                    payload=payload,
                    event_context=ContextMeta(
                        summary=(
                            f"{payload['coin']}: R$ {payload['price']:,.2f} "
                            f"({payload['change_pct']:+.2f}%)"
                        ),
                        model="rule-based-v1",
                    ),
                ))

        return events


# ── Copom Ingestor ────────────────────────────────────────


class CopomIngestor(BaseIngestor):
    content_type = FinanceContentTypes.COPOM

    def __init__(self, signer: Any, last_n: int = 1) -> None:
        super().__init__(signer)
        self.last_n = last_n

    async def fetch(self) -> list[CDSEvent]:
        events: list[CDSEvent] = []
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(COPOM_URL)
            resp.raise_for_status()
            fp = _fingerprint(resp.content)
            data = resp.json()

            meetings = data.get("conteudo", [])[:self.last_n]
            for item in meetings:
                rate_after = float(item.get("metaSelic", 0))
                rate_before = float(item.get("metaSelicAnterior", rate_after))
                diff_bps = round((rate_after - rate_before) * 100)

                if diff_bps > 0:
                    decision = "raise"
                elif diff_bps < 0:
                    decision = "cut"
                else:
                    decision = "maintain"

                meeting_date = item.get("dataReuniao", "")
                copom = CopomDecision(
                    meeting_number=int(item.get("numeroReuniao", 0)),
                    meeting_date=meeting_date,
                    decision=decision,
                    rate_before=rate_before,
                    rate_after=rate_after,
                    rate_change_bps=diff_bps,
                    vote_unanimous=item.get("unanime", True),
                    statement_url=item.get("urlAta"),
                )
                try:
                    occurred = datetime.fromisoformat(f"{meeting_date}T18:30:00-03:00")
                except (ValueError, TypeError):
                    occurred = datetime.now(UTC)

                events.append(CDSEvent(
                    content_type=FinanceContentTypes.COPOM,
                    source=SourceMeta(id=CDSSources.BCB_API, fingerprint=fp),
                    occurred_at=occurred,
                    lang="pt-BR",
                    payload=copom.model_dump(mode="json"),
                    event_context=ContextMeta(
                        summary=(
                            f"Copom #{copom.meeting_number}: "
                            f"{copom.decision} SELIC em {copom.rate_after}% a.a."
                        ),
                        model="rule-based-v1",
                    ),
                ))

        return events
