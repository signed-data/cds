"""SignedData CDS Python SDK v0.3.0"""

from cds.ingestor import BaseIngestor
from cds.schema import CDSEvent, ContextMeta, IntegrityMeta, SourceMeta
from cds.signer import CDSSigner, CDSVerifier, generate_keypair
from cds.sources.commodities_models import (
    CommodityContentTypes,
    CommodityFutures,
    CommodityIndex,
    CommoditySpot,
)
from cds.sources.companies_models import (
    CNAECode,
    CompaniesContentTypes,
    CompanyAddress,
    CompanyPartner,
    CompanyPartners,
    CompanyProfile,
)
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
from cds.sources.football_models import (
    FootballContentTypes,
    FootballMatchPayload,
    FootballTeam,
    FootballVenue,
)
from cds.sources.lottery_models import (
    LotteryContentTypes,
    LotteryResult,
    MegaSenaResult,
    PrizeTier,
)
from cds.vocab import (
    CONTEXT_URI,
    EVENT_TYPE_URI,
    PUBLIC_KEY_URI,
    CDSSources,
    CDSVocab,
    content_type_uri,
    event_uri,
    source_uri,
)

__version__ = "0.3.0"

__all__ = [
    "CDSEvent", "SourceMeta", "ContextMeta", "IntegrityMeta",
    "CDSSigner", "CDSVerifier", "generate_keypair",
    "BaseIngestor",
    "CDSVocab", "CDSSources",
    "content_type_uri", "source_uri", "event_uri",
    "CONTEXT_URI", "EVENT_TYPE_URI", "PUBLIC_KEY_URI",
    # lottery
    "LotteryContentTypes", "MegaSenaResult", "LotteryResult", "PrizeTier",
    # football
    "FootballContentTypes", "FootballMatchPayload", "FootballVenue", "FootballTeam",
    # finance.brazil
    "FinanceContentTypes", "SELICRate", "CDIRate", "IPCAIndex", "IGPMIndex",
    "FXRate", "StockQuote", "CopomDecision",
    # companies.brazil
    "CompaniesContentTypes", "CompanyProfile", "CompanyPartners",
    "CompanyAddress", "CompanyPartner", "CNAECode",
    # commodities.brazil
    "CommodityContentTypes", "CommodityFutures", "CommoditySpot", "CommodityIndex",
]
