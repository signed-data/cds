/**
 * CDS Vocabulary — URI constants for all CDS entities.
 * TypeScript mirror of sdk/python/cds/vocab.py
 */

const BASE = "https://signed-data.org";

export const CDS_CONTEXT_URI     = `${BASE}/contexts/cds/v1.jsonld`;
export const CDS_EVENT_TYPE_URI  = `${BASE}/vocab/CuratedDataEvent`;
export const CDS_SOURCE_TYPE_URI = `${BASE}/vocab/DataSource`;
export const CDS_PUBLIC_KEY_URI  = `${BASE}/.well-known/cds-public-key.pem`;

export const eventUri      = (id: string)     => `${BASE}/events/${id}`;
export const sourceUri     = (slug: string)   => `${BASE}/sources/${slug}`;
export const contentTypeUri = (domain: string, schema: string) =>
  `${BASE}/vocab/${domain.replace(/\./g, "-")}/${schema.replace(/\./g, "-")}`;

export const CDSVocab = {
  WEATHER_CURRENT:       contentTypeUri("weather",          "forecast.current"),
  WEATHER_DAILY:         contentTypeUri("weather",          "forecast.daily"),
  WEATHER_ALERT:         contentTypeUri("weather",          "alert.severe"),
  FOOTBALL_MATCH_RESULT: contentTypeUri("sports.football",  "match.result"),
  FOOTBALL_MATCH_LIVE:   contentTypeUri("sports.football",  "match.live"),
  FOOTBALL_STANDINGS:    contentTypeUri("sports.football",  "standings.update"),
  NEWS_HEADLINE:         contentTypeUri("news",             "headline"),
  NEWS_BREAKING:         contentTypeUri("news",             "breaking"),
  FINANCE_STOCK:         contentTypeUri("finance",          "quote.stock"),
  FINANCE_CRYPTO:        contentTypeUri("finance",          "quote.crypto"),
  FINANCE_FOREX:         contentTypeUri("finance",          "quote.forex"),
  LOTTERY_MEGA_SENA:     contentTypeUri("lottery.brazil",   "mega-sena.result"),
  LOTTERY_LOTOFACIL:     contentTypeUri("lottery.brazil",   "lotofacil.result"),
  LOTTERY_QUINA:         contentTypeUri("lottery.brazil",   "quina.result"),
  LOTTERY_LOTOMANIA:     contentTypeUri("lottery.brazil",   "lotomania.result"),
  LOTTERY_DUPLA_SENA:    contentTypeUri("lottery.brazil",   "dupla-sena.result"),
  BIBLE_VERSE:           contentTypeUri("religion.bible",   "verse"),
  BIBLE_DAILY:           contentTypeUri("religion.bible",   "daily"),
  GOV_BR_DIARIO:         contentTypeUri("government.brazil","diario.oficial"),
  // finance.brazil
  FINANCE_SELIC_RATE:     contentTypeUri("finance.brazil", "rate.selic"),
  FINANCE_CDI_RATE:       contentTypeUri("finance.brazil", "rate.cdi"),
  FINANCE_IPCA_INDEX:     contentTypeUri("finance.brazil", "index.ipca"),
  FINANCE_IGPM_INDEX:     contentTypeUri("finance.brazil", "index.igpm"),
  FINANCE_FX_USD_BRL:     contentTypeUri("finance.brazil", "fx.usd-brl"),
  FINANCE_FX_EUR_BRL:     contentTypeUri("finance.brazil", "fx.eur-brl"),
  FINANCE_QUOTE_STOCK:    contentTypeUri("finance.brazil", "quote.stock"),
  FINANCE_QUOTE_FII:      contentTypeUri("finance.brazil", "quote.fii"),
  FINANCE_QUOTE_CRYPTO:   contentTypeUri("finance.brazil", "quote.crypto"),
  FINANCE_DECISION_COPOM: contentTypeUri("finance.brazil", "decision.copom"),
  // companies.brazil
  COMPANIES_PROFILE_CNPJ:  contentTypeUri("companies.brazil", "profile.cnpj"),
  COMPANIES_PARTNERS_CNPJ: contentTypeUri("companies.brazil", "partners.cnpj"),
  COMPANIES_CNAE_PROFILE:  contentTypeUri("companies.brazil", "cnae.profile"),
  // commodities.brazil
  COMMODITY_FUTURES_SOJA:    contentTypeUri("commodities.brazil", "futures.soja"),
  COMMODITY_FUTURES_MILHO:   contentTypeUri("commodities.brazil", "futures.milho"),
  COMMODITY_FUTURES_BOI:     contentTypeUri("commodities.brazil", "futures.boi-gordo"),
  COMMODITY_FUTURES_CAFE:    contentTypeUri("commodities.brazil", "futures.cafe"),
  COMMODITY_FUTURES_ACUCAR:  contentTypeUri("commodities.brazil", "futures.acucar"),
  COMMODITY_FUTURES_ETANOL:  contentTypeUri("commodities.brazil", "futures.etanol"),
  COMMODITY_SPOT_SOJA:       contentTypeUri("commodities.brazil", "spot.soja"),
  COMMODITY_SPOT_MILHO:      contentTypeUri("commodities.brazil", "spot.milho"),
  COMMODITY_SPOT_TRIGO:      contentTypeUri("commodities.brazil", "spot.trigo"),
  COMMODITY_SPOT_ALGODAO:    contentTypeUri("commodities.brazil", "spot.algodao"),
  COMMODITY_INDEX_WORLDBANK: contentTypeUri("commodities.brazil", "index.worldbank"),
} as const;

export const CDSSources = {
  CAIXA_LOTERIAS: sourceUri("caixa.gov.br.loterias.v1"),
  API_FOOTBALL:   sourceUri("api-football.com.v3"),
  OPEN_METEO:     sourceUri("open-meteo.com.v1"),
  BRAPI:          sourceUri("brapi.dev.v1"),
  BIBLE_API:      sourceUri("bible-api.com.v1"),
  BCB_API:        sourceUri("api.bcb.gov.br.v1"),
  BRASILAPI:      sourceUri("brasilapi.com.br.v1"),
  CONAB:          sourceUri("conab.gov.br.v1"),
  WORLDBANK:      sourceUri("api.worldbank.org.v2"),
} as const;
