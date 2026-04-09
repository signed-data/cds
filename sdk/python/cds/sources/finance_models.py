"""
SignedData CDS — Finance Brazil Domain Models
Typed Pydantic payload schemas for finance.brazil events.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from cds.vocab import CDSVocab


class FinanceContentTypes:
    SELIC    = CDSVocab.FINANCE_SELIC_RATE
    CDI      = CDSVocab.FINANCE_CDI_RATE
    IPCA     = CDSVocab.FINANCE_IPCA_INDEX
    IGPM     = CDSVocab.FINANCE_IGPM_INDEX
    USD_BRL  = CDSVocab.FINANCE_FX_USD_BRL
    EUR_BRL  = CDSVocab.FINANCE_FX_EUR_BRL
    STOCK    = CDSVocab.FINANCE_QUOTE_STOCK
    FII      = CDSVocab.FINANCE_QUOTE_FII
    CRYPTO   = CDSVocab.FINANCE_QUOTE_CRYPTO
    COPOM    = CDSVocab.FINANCE_DECISION_COPOM


class SELICRate(BaseModel):
    date: str               # "2026-04-02"
    rate_annual: float      # 13.75
    rate_daily: float       # computed: (1 + rate_annual/100)^(1/252) - 1
    unit: str = "% a.a."
    effective_date: str


class CDIRate(BaseModel):
    date: str
    rate_annual: float
    rate_daily: float
    unit: str = "% a.a."


class IPCAIndex(BaseModel):
    date: str
    monthly_pct: float
    accumulated_12m: float
    accumulated_year: float
    base_year: int = 1993


class IGPMIndex(BaseModel):
    date: str
    monthly_pct: float


class FXRate(BaseModel):
    date: str
    buy: float
    sell: float
    mid: float              # computed: (buy + sell) / 2
    currency_from: str
    currency_to: str
    source: str = "ptax"


class StockQuote(BaseModel):
    ticker: str
    short_name: str
    long_name: str
    currency: str
    market_price: float
    change: float
    change_pct: float
    previous_close: float
    open: float | None = None
    day_high: float
    day_low: float
    volume: int
    market_cap: int | None = None
    exchange: str
    market_state: str       # "REGULAR", "PRE", "POST", "CLOSED"
    timestamp: str


class CopomDecision(BaseModel):
    meeting_number: int
    meeting_date: str
    decision: Literal["raise", "cut", "maintain"]
    rate_before: float
    rate_after: float
    rate_change_bps: int    # basis points: raise=+25, cut=-25, maintain=0
    vote_unanimous: bool
    statement_url: str | None = None
