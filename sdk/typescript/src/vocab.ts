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
} as const;

export const CDSSources = {
  CAIXA_LOTERIAS: sourceUri("caixa.gov.br.loterias.v1"),
  API_FOOTBALL:   sourceUri("api-football.com.v3"),
  OPEN_METEO:     sourceUri("open-meteo.com.v1"),
  BRAPI:          sourceUri("brapi.dev.v1"),
  BIBLE_API:      sourceUri("bible-api.com.v1"),
} as const;
