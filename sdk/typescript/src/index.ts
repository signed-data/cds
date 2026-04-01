export { CDSEvent, CDSContentType } from "./schema.js";
export type { SourceMeta, ContextMeta, IntegrityMeta, CDSEventOptions } from "./schema.js";
export { CDSSigner, CDSVerifier, generateKeypair } from "./signer.js";
export { BaseIngestor } from "./ingestor.js";
export { FootballIngestor, FootballContentTypes, LEAGUE_IDS } from "./sources/football.js";
export type {
  FootballMatchPayload, FootballStandingsPayload,
  FootballTeam, FootballVenue, MatchStatus,
} from "./sources/football.js";
export { MegaSenaIngestor, LotteryContentTypes } from "./sources/lottery.js";
export type { MegaSenaResult, MegaSenaIngestorOptions, PrizeTier } from "./sources/lottery.js";
