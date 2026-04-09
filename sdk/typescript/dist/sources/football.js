/**
 * SignedData CDS — Football Source
 * Source: api-football.com (RapidAPI)
 */
import { createHash } from "node:crypto";
import { CDSContentType, CDSEvent } from "../schema.js";
import { BaseIngestor } from "../ingestor.js";
export const FootballContentTypes = {
    MATCH_RESULT: new CDSContentType({ domain: "sports.football", schema_name: "match.result" }),
    MATCH_LIVE: new CDSContentType({ domain: "sports.football", schema_name: "match.live" }),
    STANDINGS: new CDSContentType({ domain: "sports.football", schema_name: "standings.update" }),
    PLAYER_STAT: new CDSContentType({ domain: "sports.football", schema_name: "player.stat" }),
};
export const LEAGUE_IDS = {
    brasileirao_a: 71, brasileirao_b: 72, copa_brasil: 73,
    libertadores: 13, sul_americana: 11,
    premier_league: 39, champions_league: 2,
};
const STATUS_MAP = {
    NS: "scheduled",
    "1H": "live", HT: "live", "2H": "live", ET: "live", BT: "live", P: "live",
    FT: "finished", AET: "finished", PEN: "finished",
    PST: "postponed", CANC: "cancelled", ABD: "cancelled",
    AWD: "finished", WO: "finished",
};
const API_BASE = "https://v3.football.api-sports.io";
function buildTeam(t, score) {
    return {
        id: t["id"],
        name: t["name"] ?? "",
        short_name: (t["name"] ?? "").slice(0, 3).toUpperCase(),
        score, logo_url: t["logo"] ?? "",
    };
}
function summary(home, away, hs, as_, status, comp, minute) {
    if (status === "finished")
        return `${comp}: ${home} ${hs} x ${as_} ${away} (finished)`;
    if (status === "live")
        return `${comp}: ${home} ${hs} x ${as_} ${away} — LIVE${minute ? ` ${minute}'` : ""}`;
    if (status === "scheduled")
        return `${comp}: ${home} vs ${away} — scheduled`;
    return `${comp}: ${home} vs ${away} (${status})`;
}
export class FootballIngestor extends BaseIngestor {
    contentType = FootballContentTypes.MATCH_RESULT;
    apiKey;
    leagueIds;
    season;
    constructor(signer, opts) {
        super(signer);
        this.apiKey = opts.apiKey;
        this.leagueIds = opts.leagueIds ?? [LEAGUE_IDS.brasileirao_a];
        this.season = opts.season ?? new Date().getFullYear();
    }
    async fetch() {
        const events = [];
        for (const leagueId of this.leagueIds) {
            const url = `${API_BASE}/fixtures?league=${leagueId}&season=${this.season}&last=10`;
            const resp = await globalThis.fetch(url, { headers: { "x-apisports-key": this.apiKey } });
            if (!resp.ok)
                throw new Error(`api-football HTTP ${resp.status}`);
            const buf = Buffer.from(await resp.arrayBuffer());
            const fp = "sha256:" + createHash("sha256").update(buf).digest("hex");
            const body = JSON.parse(buf.toString("utf-8"));
            for (const f of body.response ?? [])
                events.push(this.buildEvent(f, fp));
        }
        return events;
    }
    buildEvent(f, fingerprint) {
        const fx = f["fixture"] ?? {};
        const teams = f["teams"] ?? {};
        const goals = f["goals"] ?? {};
        const lg = f["league"] ?? {};
        const venue = (fx["venue"] ?? {});
        const fxSt = fx["status"] ?? {};
        const hs = goals["home"] ?? null;
        const as_ = goals["away"] ?? null;
        const status = STATUS_MAP[fxSt["short"] ?? "NS"] ?? "scheduled";
        const minute = fxSt["elapsed"];
        const homeTeam = buildTeam(teams["home"] ?? {}, hs);
        const awayTeam = buildTeam(teams["away"] ?? {}, as_);
        const comp = lg["name"] ?? "";
        const ct = status === "live" ? FootballContentTypes.MATCH_LIVE : FootballContentTypes.MATCH_RESULT;
        const payload = {
            match_id: fx["id"],
            home: homeTeam, away: awayTeam, status, competition: comp,
            competition_id: lg["id"],
            season: String(lg["season"] ?? this.season),
            matchday: lg["round"]?.replace("Regular Season - ", "") || undefined,
            venue: { name: venue["name"] ?? "", city: venue["city"] ?? "", country: "" },
            minute, referee: fx["referee"] ?? "",
            match_date: (fx["date"] ?? "").slice(0, 10),
        };
        return new CDSEvent({
            content_type: ct,
            source: { id: "api-football.com.v3", fingerprint },
            occurred_at: fx["date"] ?? new Date().toISOString(),
            lang: "en",
            payload: payload,
            context: {
                summary: summary(homeTeam.name, awayTeam.name, hs, as_, status, comp, minute),
                model: "rule-based-v1",
                generated_at: new Date().toISOString(),
            },
        });
    }
}
//# sourceMappingURL=football.js.map