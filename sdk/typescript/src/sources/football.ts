/**
 * SignedData CDS — Football Source
 * Source: api-football.com (RapidAPI)
 */

import { createHash } from "node:crypto";
import { CDSEvent, ContextMeta, SourceMeta } from "../schema.js";
import type { CDSSigner } from "../signer.js";
import { BaseIngestor } from "../ingestor.js";
import { CDSVocab, CDSSources } from "../vocab.js";

export const FootballContentTypes = {
  MATCH_RESULT: CDSVocab.FOOTBALL_MATCH_RESULT,
  MATCH_LIVE:   CDSVocab.FOOTBALL_MATCH_LIVE,
  STANDINGS:    CDSVocab.FOOTBALL_STANDINGS,
} as const;

export const LEAGUE_IDS = {
  brasileirao_a: 71, brasileirao_b: 72, copa_brasil: 73,
  libertadores: 13, sul_americana: 11,
  premier_league: 39, champions_league: 2,
} as const;

export type MatchStatus = "scheduled" | "live" | "finished" | "postponed" | "cancelled";

export interface FootballTeam {
  id?: number; name: string; short_name: string;
  score: number | null; logo_url: string;
}
export interface FootballVenue { name: string; city: string; country: string; }
export interface FootballMatchPayload {
  match_id?: number; home: FootballTeam; away: FootballTeam;
  status: MatchStatus; competition: string; competition_id?: number;
  season: string; matchday?: string; venue: FootballVenue;
  minute?: number; referee: string; match_date: string;
}
export interface StandingsEntry {
  position: number; team: FootballTeam;
  played: number; won: number; drawn: number; lost: number;
  goals_for: number; goals_against: number; goal_diff: number;
  points: number; form: string;
}
export interface FootballStandingsPayload {
  competition: string; competition_id?: number; season: string;
  table: StandingsEntry[];
}

const STATUS_MAP: Record<string, MatchStatus> = {
  NS: "scheduled",
  "1H": "live", HT: "live", "2H": "live", ET: "live", BT: "live", P: "live",
  FT: "finished", AET: "finished", PEN: "finished",
  PST: "postponed", CANC: "cancelled", ABD: "cancelled",
  AWD: "finished", WO: "finished",
};

const API_BASE = "https://v3.football.api-sports.io";
type R = Record<string, unknown>;

function buildTeam(t: R, score: number | null): FootballTeam {
  return {
    id: t["id"] as number | undefined,
    name: (t["name"] as string) ?? "",
    short_name: ((t["name"] as string) ?? "").slice(0, 3).toUpperCase(),
    score, logo_url: (t["logo"] as string) ?? "",
  };
}

function summary(
  home: string, away: string, hs: number | null, as_: number | null,
  status: MatchStatus, comp: string, minute?: number
): string {
  if (status === "finished") return `${comp}: ${home} ${hs} x ${as_} ${away} (finished)`;
  if (status === "live")     return `${comp}: ${home} ${hs} x ${as_} ${away} — LIVE${minute ? ` ${minute}'` : ""}`;
  if (status === "scheduled") return `${comp}: ${home} vs ${away} — scheduled`;
  return `${comp}: ${home} vs ${away} (${status})`;
}

export interface FootballIngestorOptions {
  apiKey: string;
  leagueIds?: number[];
  season?: number;
}

export class FootballIngestor extends BaseIngestor {
  readonly contentType = FootballContentTypes.MATCH_RESULT;
  private readonly apiKey: string;
  private readonly leagueIds: number[];
  private readonly season: number;

  constructor(signer: CDSSigner, opts: FootballIngestorOptions) {
    super(signer);
    this.apiKey    = opts.apiKey;
    this.leagueIds = opts.leagueIds ?? [LEAGUE_IDS.brasileirao_a];
    this.season    = opts.season ?? new Date().getFullYear();
  }

  async fetch(): Promise<CDSEvent[]> {
    const events: CDSEvent[] = [];
    for (const leagueId of this.leagueIds) {
      const url  = `${API_BASE}/fixtures?league=${leagueId}&season=${this.season}&last=10`;
      const resp = await globalThis.fetch(url, { headers: { "x-apisports-key": this.apiKey } });
      if (!resp.ok) throw new Error(`api-football HTTP ${resp.status}`);
      const buf  = Buffer.from(await resp.arrayBuffer());
      const fp   = "sha256:" + createHash("sha256").update(buf).digest("hex");
      const body = JSON.parse(buf.toString("utf-8")) as { response: R[] };
      for (const f of body.response ?? []) events.push(this.buildEvent(f, fp));
    }
    return events;
  }

  private buildEvent(f: R, fingerprint: string): CDSEvent {
    const fx    = (f["fixture"] as R) ?? {};
    const teams = (f["teams"]   as Record<string, R>) ?? {};
    const goals = (f["goals"]   as Record<string, number | null>) ?? {};
    const lg    = (f["league"]  as R) ?? {};
    const venue = ((fx["venue"] as R) ?? {}) as Record<string, string>;
    const fxSt  = (fx["status"] as Record<string, unknown>) ?? {};

    const hs     = goals["home"] ?? null;
    const as_    = goals["away"] ?? null;
    const status: MatchStatus = STATUS_MAP[(fxSt["short"] as string) ?? "NS"] ?? "scheduled";
    const minute = fxSt["elapsed"] as number | undefined;

    const homeTeam = buildTeam(teams["home"] ?? {}, hs);
    const awayTeam = buildTeam(teams["away"] ?? {}, as_);
    const comp     = (lg["name"] as string) ?? "";
    const ct       = status === "live" ? FootballContentTypes.MATCH_LIVE : FootballContentTypes.MATCH_RESULT;

    const payload: FootballMatchPayload = {
      match_id: fx["id"] as number | undefined,
      home: homeTeam, away: awayTeam, status, competition: comp,
      competition_id: lg["id"] as number | undefined,
      season: String(lg["season"] ?? this.season),
      matchday: (lg["round"] as string)?.replace("Regular Season - ", "") || undefined,
      venue: { name: venue["name"] ?? "", city: venue["city"] ?? "", country: "" },
      minute, referee: (fx["referee"] as string) ?? "",
      match_date: ((fx["date"] as string) ?? "").slice(0, 10),
    };

    return new CDSEvent({
      content_type: ct,
      source: { "@id": CDSSources.API_FOOTBALL, fingerprint },
      occurred_at: (fx["date"] as string) ?? new Date().toISOString(),
      lang: "en",
      payload: payload as unknown as R,
      context: {
        summary: summary(homeTeam.name, awayTeam.name, hs, as_, status, comp, minute),
        model: "rule-based-v1",
        generated_at: new Date().toISOString(),
      },
    });
  }
}
