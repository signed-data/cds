"""SignedData CDS Python SDK v0.2.0"""

from cds.schema import CDSEvent, SourceMeta, ContextMeta, IntegrityMeta
from cds.signer import CDSSigner, CDSVerifier, generate_keypair
from cds.ingestor import BaseIngestor
from cds.vocab import (
    CDSVocab, CDSSources,
    content_type_uri, source_uri, event_uri,
    CONTEXT_URI, EVENT_TYPE_URI, PUBLIC_KEY_URI,
)
from cds.sources.lottery_models import (
    LotteryContentTypes, MegaSenaResult, LotteryResult, PrizeTier,
)
from cds.sources.football_models import (
    FootballContentTypes, FootballMatchPayload, FootballVenue, FootballTeam,
)

__version__ = "0.2.0"

__all__ = [
    "CDSEvent", "SourceMeta", "ContextMeta", "IntegrityMeta",
    "CDSSigner", "CDSVerifier", "generate_keypair",
    "BaseIngestor",
    "CDSVocab", "CDSSources",
    "content_type_uri", "source_uri", "event_uri",
    "CONTEXT_URI", "EVENT_TYPE_URI", "PUBLIC_KEY_URI",
    "LotteryContentTypes", "MegaSenaResult", "LotteryResult", "PrizeTier",
    "FootballContentTypes", "FootballMatchPayload", "FootballVenue", "FootballTeam",
]
