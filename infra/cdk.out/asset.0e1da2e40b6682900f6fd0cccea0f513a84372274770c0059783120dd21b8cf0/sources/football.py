"""
SignedData CDS — Football Ingestor
Source: api-football.com (RapidAPI free plan: 100 req/day)
Docs:   https://www.api-football.com/documentation-v3

Usage:
    ingestor = FootballIngestor(
        signer=signer,
        api_key="YOUR_RAPIDAPI_KEY",
        league_ids=[71],   # 71 = Brasileirão Série A
        season=2026,
    )
    events = await ingestor.ingest()
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import httpx

from cds.ingestor import BaseIngestor
from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.sources.football_models import (
    FootballContentTypes,
    FootballMatchPayload,
    FootballTeam,
    FootballVenue,
)

API_BASE = "https://v3.football.api-sports.io"

LEAGUE_IDS: dict[str, int] = {
    "brasileirao_a":    71,
    "brasileirao_b":    72,
    "copa_brasil":      73,
    "libertadores":     13,
    "sul_americana":    11,
    "premier_league":   39,
    "champions_league": 2,
}

STATUS_MAP: dict[str, str] = {
    "NS": "scheduled",
    "1H": "live", "HT": "live", "2H": "live",
    "ET": "live", "BT": "live", "P": "live",
    "FT": "finished", "AET": "finished", "PEN": "finished",
    "PST": "postponed", "CANC": "cancelled", "ABD": "cancelled",
    "AWD": "finished", "WO": "finished",
}


def _summary(
    home: str, away: str,
    hs: int | None, as_: int | None,
    status: str, competition: str,
    minute: int | None,
) -> str:
    if status == "finished":
        return f"{competition}: {home} {hs} x {as_} {away} (finished)"
    if status == "live":
        m = f" {minute}'" if minute else ""
        return f"{competition}: {home} {hs} x {as_} {away} — LIVE{m}"
    if status == "scheduled":
        return f"{competition}: {home} vs {away} — scheduled"
    return f"{competition}: {home} vs {away} ({status})"


def _team(t: dict[str, Any]) -> FootballTeam:
    return FootballTeam(
        id=t.get("id"),
        name=t.get("name", ""),
        short_name=(t.get("name") or "")[:3].upper(),
        logo_url=t.get("logo", ""),
    )


class FootballIngestor(BaseIngestor):
    content_type = FootballContentTypes.MATCH_RESULT

    def __init__(
        self,
        signer: Any,
        api_key: str,
        league_ids: list[int] | None = None,
        season: int | None = None,
    ) -> None:
        super().__init__(signer)
        self.api_key    = api_key
        self.league_ids = league_ids or [LEAGUE_IDS["brasileirao_a"]]
        self.season     = season or datetime.now(timezone.utc).year

    async def fetch(self) -> list[CDSEvent]:
        events: list[CDSEvent] = []
        async with httpx.AsyncClient(timeout=15) as client:
            for league_id in self.league_ids:
                resp = await client.get(
                    f"{API_BASE}/fixtures",
                    headers={"x-apisports-key": self.api_key},
                    params={"league": league_id, "season": self.season, "last": 10},
                )
                resp.raise_for_status()
                fp = "sha256:" + hashlib.sha256(resp.content).hexdigest()
                for fixture in resp.json().get("response", []):
                    events.append(self._build_event(fixture, fp))
        return events

    def _build_event(self, f: dict[str, Any], fingerprint: str) -> CDSEvent:
        fx     = f["fixture"]
        teams  = f["teams"]
        goals  = f["goals"]
        league = f["league"]
        venue  = fx.get("venue", {})

        hs     = goals.get("home")
        as_    = goals.get("away")
        status = STATUS_MAP.get(fx.get("status", {}).get("short", "NS"), "scheduled")
        minute = fx.get("status", {}).get("elapsed")

        home_team       = _team(teams["home"]); home_team.score = hs
        away_team       = _team(teams["away"]); away_team.score = as_
        competition     = league.get("name", "")

        ct = (
            FootballContentTypes.MATCH_LIVE
            if status == "live"
            else FootballContentTypes.MATCH_RESULT
        )

        payload = FootballMatchPayload(
            match_id=fx.get("id"),
            home=home_team, away=away_team,
            status=status,  # type: ignore[arg-type]
            competition=competition,
            competition_id=league.get("id"),
            season=str(league.get("season", self.season)),
            matchday=(league.get("round") or "").replace("Regular Season - ", "") or None,
            venue=FootballVenue(name=venue.get("name", ""), city=venue.get("city", "")),
            minute=minute,
            referee=fx.get("referee", ""),
            match_date=(fx.get("date") or "")[:10],
        )

        return CDSEvent(
            content_type=ct,
            source=SourceMeta(id="api-football.com.v3", fingerprint=fingerprint),
            occurred_at=datetime.fromisoformat(
                fx["date"].replace("Z", "+00:00")
            ) if fx.get("date") else datetime.now(timezone.utc),
            lang="en",
            payload=payload.model_dump(mode="json"),
            context=ContextMeta(
                summary=_summary(home_team.name, away_team.name, hs, as_, status, competition, minute),
                model="rule-based-v1",
            ),
        )
