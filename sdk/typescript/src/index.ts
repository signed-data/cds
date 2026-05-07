export { CDSEvent }                  from "./schema.js";
export type { SourceMeta, ContextMeta, IntegrityMeta, CDSEventOptions } from "./schema.js";
export { CDSSigner, CDSVerifier, generateKeypair }  from "./signer.js";
export { BaseIngestor }              from "./ingestor.js";
export { CDSVocab, CDSSources, contentTypeUri, sourceUri, eventUri,
         CDS_CONTEXT_URI, CDS_EVENT_TYPE_URI, CDS_PUBLIC_KEY_URI } from "./vocab.js";
export { MegaSenaIngestor, LotteryContentTypes } from "./sources/lottery.js";
export type { MegaSenaResult, PrizeTier as LotteryPrizeTier } from "./sources/lottery.js";
export { FootballIngestor, FootballContentTypes, LEAGUE_IDS } from "./sources/football.js";
export type { FootballMatchPayload, FootballTeam, FootballVenue } from "./sources/football.js";
// finance.brazil
export { FinanceContentTypes, BCBRatesIngestor, BrapiQuotesIngestor } from "./sources/finance.js";
export type { SELICRate, CDIRate, IPCAIndex, IGPMIndex, FXRate, StockQuote, CopomDecision } from "./sources/finance.js";
// companies.brazil
export { CompaniesContentTypes, CNPJFetcher, validateCnpj, formatCnpj } from "./sources/companies.js";
export type { CompanyProfile, CompanyPartners, CompanyPartner, CompanyAddress, CNAECode } from "./sources/companies.js";
// commodities.brazil
export { CommodityContentTypes, B3FuturesIngestor, B3_COMMODITY_TICKERS } from "./sources/commodities.js";
export type { CommodityFutures, CommoditySpot, CommodityIndex } from "./sources/commodities.js";
