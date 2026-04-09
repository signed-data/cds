"""
CDS Vocabulary — URI constants for all CDS entities.
Use these constants everywhere instead of constructing URI strings manually.
"""
from __future__ import annotations

_BASE = "https://signed-data.org"

# ── Core endpoints ─────────────────────────────────────────

CONTEXT_URI     = f"{_BASE}/contexts/cds/v1.jsonld"
VOCAB_URI       = f"{_BASE}/vocab/"
EVENT_TYPE_URI  = f"{_BASE}/vocab/CuratedDataEvent"
SOURCE_TYPE_URI = f"{_BASE}/vocab/DataSource"
PUBLIC_KEY_URI  = f"{_BASE}/.well-known/cds-public-key.pem"


# ── URI builders ───────────────────────────────────────────

def event_uri(event_id: str) -> str:
    """'a3f8c2d1-...' → 'https://signed-data.org/events/a3f8c2d1-...'"""
    return f"{_BASE}/events/{event_id}"


def source_uri(source_slug: str) -> str:
    """
    'caixa.gov.br.loterias.v1'
    → 'https://signed-data.org/sources/caixa.gov.br.loterias.v1'
    Dots are KEPT in source URIs.
    """
    return f"{_BASE}/sources/{source_slug}"


def content_type_uri(domain: str, schema_name: str) -> str:
    """
    ('lottery.brazil', 'mega-sena.result')
    → 'https://signed-data.org/vocab/lottery-brazil/mega-sena-result'
    ALL dots become hyphens in both domain and schema_name.
    """
    return f"{_BASE}/vocab/{domain.replace('.', '-')}/{schema_name.replace('.', '-')}"


# ── Pre-built content type URI constants ───────────────────

class CDSVocab:
    # weather
    WEATHER_CURRENT = content_type_uri("weather", "forecast.current")
    WEATHER_DAILY   = content_type_uri("weather", "forecast.daily")
    WEATHER_ALERT   = content_type_uri("weather", "alert.severe")
    # sports.football
    FOOTBALL_MATCH_RESULT  = content_type_uri("sports.football", "match.result")
    FOOTBALL_MATCH_LIVE    = content_type_uri("sports.football", "match.live")
    FOOTBALL_STANDINGS     = content_type_uri("sports.football", "standings.update")
    # news
    NEWS_HEADLINE = content_type_uri("news", "headline")
    NEWS_BREAKING = content_type_uri("news", "breaking")
    NEWS_SUMMARY  = content_type_uri("news", "summary")
    # finance
    FINANCE_STOCK  = content_type_uri("finance", "quote.stock")
    FINANCE_CRYPTO = content_type_uri("finance", "quote.crypto")
    FINANCE_FOREX  = content_type_uri("finance", "quote.forex")
    FINANCE_INDEX  = content_type_uri("finance", "index.update")
    # lottery.brazil
    LOTTERY_MEGA_SENA  = content_type_uri("lottery.brazil", "mega-sena.result")
    LOTTERY_LOTOFACIL  = content_type_uri("lottery.brazil", "lotofacil.result")
    LOTTERY_QUINA      = content_type_uri("lottery.brazil", "quina.result")
    LOTTERY_LOTOMANIA  = content_type_uri("lottery.brazil", "lotomania.result")
    LOTTERY_DUPLA_SENA = content_type_uri("lottery.brazil", "dupla-sena.result")
    # religion.bible
    BIBLE_VERSE   = content_type_uri("religion.bible", "verse")
    BIBLE_PASSAGE = content_type_uri("religion.bible", "passage")
    BIBLE_DAILY   = content_type_uri("religion.bible", "daily")
    # government.brazil
    GOV_BR_DIARIO    = content_type_uri("government.brazil", "diario.oficial")
    GOV_BR_LICITACAO = content_type_uri("government.brazil", "licitacao")
    GOV_BR_LEI       = content_type_uri("government.brazil", "lei")
    # finance.brazil
    FINANCE_SELIC_RATE     = content_type_uri("finance.brazil", "rate.selic")
    FINANCE_CDI_RATE       = content_type_uri("finance.brazil", "rate.cdi")
    FINANCE_IPCA_INDEX     = content_type_uri("finance.brazil", "index.ipca")
    FINANCE_IGPM_INDEX     = content_type_uri("finance.brazil", "index.igpm")
    FINANCE_FX_USD_BRL     = content_type_uri("finance.brazil", "fx.usd-brl")
    FINANCE_FX_EUR_BRL     = content_type_uri("finance.brazil", "fx.eur-brl")
    FINANCE_QUOTE_STOCK    = content_type_uri("finance.brazil", "quote.stock")
    FINANCE_QUOTE_FII      = content_type_uri("finance.brazil", "quote.fii")
    FINANCE_QUOTE_CRYPTO   = content_type_uri("finance.brazil", "quote.crypto")
    FINANCE_DECISION_COPOM = content_type_uri("finance.brazil", "decision.copom")
    # companies.brazil
    COMPANIES_PROFILE_CNPJ  = content_type_uri("companies.brazil", "profile.cnpj")
    COMPANIES_PARTNERS_CNPJ = content_type_uri("companies.brazil", "partners.cnpj")
    COMPANIES_CNAE_PROFILE  = content_type_uri("companies.brazil", "cnae.profile")
    # commodities.brazil
    COMMODITY_FUTURES_SOJA    = content_type_uri("commodities.brazil", "futures.soja")
    COMMODITY_FUTURES_MILHO   = content_type_uri("commodities.brazil", "futures.milho")
    COMMODITY_FUTURES_BOI     = content_type_uri("commodities.brazil", "futures.boi-gordo")
    COMMODITY_FUTURES_CAFE    = content_type_uri("commodities.brazil", "futures.cafe")
    COMMODITY_FUTURES_ACUCAR  = content_type_uri("commodities.brazil", "futures.acucar")
    COMMODITY_FUTURES_ETANOL  = content_type_uri("commodities.brazil", "futures.etanol")
    COMMODITY_SPOT_SOJA       = content_type_uri("commodities.brazil", "spot.soja")
    COMMODITY_SPOT_MILHO      = content_type_uri("commodities.brazil", "spot.milho")
    COMMODITY_SPOT_TRIGO      = content_type_uri("commodities.brazil", "spot.trigo")
    COMMODITY_SPOT_ALGODAO    = content_type_uri("commodities.brazil", "spot.algodao")
    COMMODITY_INDEX_WORLDBANK = content_type_uri("commodities.brazil", "index.worldbank")


# ── Pre-built source URI constants ─────────────────────────

class CDSSources:
    CAIXA_LOTERIAS = source_uri("caixa.gov.br.loterias.v1")
    API_FOOTBALL   = source_uri("api-football.com.v3")
    OPEN_METEO     = source_uri("open-meteo.com.v1")
    BRAPI          = source_uri("brapi.dev.v1")
    BIBLE_API      = source_uri("bible-api.com.v1")
    BCB_API        = source_uri("api.bcb.gov.br.v1")
    BRASILAPI      = source_uri("brasilapi.com.br.v1")
    CONAB          = source_uri("conab.gov.br.v1")
    WORLDBANK      = source_uri("api.worldbank.org.v2")
