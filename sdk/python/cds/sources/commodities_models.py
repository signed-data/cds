"""
SignedData CDS — Commodities Brazil Domain Models
Typed Pydantic payload schemas for commodities.brazil events.
"""
from __future__ import annotations

from pydantic import BaseModel

from cds.vocab import CDSVocab


class CommodityContentTypes:
    FUTURES_SOJA    = CDSVocab.COMMODITY_FUTURES_SOJA
    FUTURES_MILHO   = CDSVocab.COMMODITY_FUTURES_MILHO
    FUTURES_BOI     = CDSVocab.COMMODITY_FUTURES_BOI
    FUTURES_CAFE    = CDSVocab.COMMODITY_FUTURES_CAFE
    FUTURES_ACUCAR  = CDSVocab.COMMODITY_FUTURES_ACUCAR
    FUTURES_ETANOL  = CDSVocab.COMMODITY_FUTURES_ETANOL
    SPOT_SOJA       = CDSVocab.COMMODITY_SPOT_SOJA
    SPOT_MILHO      = CDSVocab.COMMODITY_SPOT_MILHO
    SPOT_TRIGO      = CDSVocab.COMMODITY_SPOT_TRIGO
    SPOT_ALGODAO    = CDSVocab.COMMODITY_SPOT_ALGODAO
    INDEX_WORLDBANK = CDSVocab.COMMODITY_INDEX_WORLDBANK


# B3 ticker → (commodity name, content type)
B3_COMMODITY_TICKERS: dict[str, tuple[str, str]] = {
    "SFI": ("soja", CommodityContentTypes.FUTURES_SOJA),
    "CCM": ("milho", CommodityContentTypes.FUTURES_MILHO),
    "BGI": ("boi gordo", CommodityContentTypes.FUTURES_BOI),
    "ICF": ("café", CommodityContentTypes.FUTURES_CAFE),
    "SWV": ("açúcar", CommodityContentTypes.FUTURES_ACUCAR),
    "ETN": ("etanol", CommodityContentTypes.FUTURES_ETANOL),
}

# CONAB commodity → content type
CONAB_COMMODITY_MAP: dict[str, str] = {
    "soja": CommodityContentTypes.SPOT_SOJA,
    "milho": CommodityContentTypes.SPOT_MILHO,
    "trigo": CommodityContentTypes.SPOT_TRIGO,
    "algodao": CommodityContentTypes.SPOT_ALGODAO,
}


class CommodityFutures(BaseModel):
    """B3 commodity futures contract quote."""
    commodity: str          # "soja", "milho", etc.
    ticker: str             # "SFI", "CCM", etc.
    exchange: str = "B3"
    unit: str               # "R$/60kg", "R$/saca", etc.
    contract_month: str     # "2026-05"
    price: float
    change: float
    change_pct: float
    open: float
    day_high: float
    day_low: float
    volume: int
    open_interest: int | None = None
    settlement_date: str | None = None
    timestamp: str


class CommoditySpot(BaseModel):
    """Physical commodity price from CONAB."""
    commodity: str          # "soja", "milho", "trigo", "algodao"
    state: str              # UF: "MT", "GO", etc.
    city: str | None = None
    unit: str               # "R$/60kg"
    price: float
    week: str               # "2026-W14"
    date_from: str
    date_to: str
    source: str = "CONAB"
    conab_notes: str | None = None


class CommodityIndex(BaseModel):
    """World Bank commodity price index."""
    indicator: str          # "PSOYBEANS", "PMAIZMT", etc.
    name: str
    date: str
    value: float
    unit: str               # "USD/mt" etc.
    source: str = "World Bank"


class CONABResponseChangedError(Exception):
    """Raised when CONAB API response structure differs from expected."""
    pass
