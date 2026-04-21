/**
 * SignedData CDS — Football Source
 * Source: api-football.com (RapidAPI)
 */
import { CDSEvent } from "../schema.js";
import { CDSSigner } from "../signer.js";
import { BaseIngestor } from "../ingestor.js";
export declare const FootballContentTypes: {
    readonly MATCH_RESULT: string;
    readonly MATCH_LIVE: string;
    readonly STANDINGS: string;
};
export declare const LEAGUE_IDS: {
    readonly brasileirao_a: 71;
    readonly brasileirao_b: 72;
    readonly copa_brasil: 73;
    readonly libertadores: 13;
    readonly sul_americana: 11;
    readonly premier_league: 39;
    readonly champions_league: 2;
};
export type MatchStatus = "scheduled" | "live" | "finished" | "postponed" | "cancelled";
export interface FootballTeam {
    id?: number;
    name: string;
    short_name: string;
    score: number | null;
    logo_url: string;
}
export interface FootballVenue {
    name: string;
    city: string;
    country: string;
}
export interface FootballMatchPayload {
    match_id?: number;
    home: FootballTeam;
    away: FootballTeam;
    status: MatchStatus;
    competition: string;
    competition_id?: number;
    season: string;
    matchday?: string;
    venue: FootballVenue;
    minute?: number;
    referee: string;
    match_date: string;
}
export interface StandingsEntry {
    position: number;
    team: FootballTeam;
    played: number;
    won: number;
    drawn: number;
    lost: number;
    goals_for: number;
    goals_against: number;
    goal_diff: number;
    points: number;
    form: string;
}
export interface FootballStandingsPayload {
    competition: string;
    competition_id?: number;
    season: string;
    table: StandingsEntry[];
}
export interface FootballIngestorOptions {
    apiKey: string;
    leagueIds?: number[];
    season?: number;
}
export declare class FootballIngestor extends BaseIngestor {
    readonly contentType: string;
    private readonly apiKey;
    private readonly leagueIds;
    private readonly season;
    constructor(signer: CDSSigner, opts: FootballIngestorOptions);
    fetch(): Promise<CDSEvent[]>;
    private buildEvent;
}
//# sourceMappingURL=football.d.ts.map