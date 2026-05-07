"""
SignedData CDS — Football Domain Models
Typed Pydantic payload schemas for sports.football events.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from cds.vocab import CDSVocab


class FootballContentTypes:
    MATCH_RESULT = CDSVocab.FOOTBALL_MATCH_RESULT
    MATCH_LIVE = CDSVocab.FOOTBALL_MATCH_LIVE
    STANDINGS = CDSVocab.FOOTBALL_STANDINGS


MatchStatus = Literal["scheduled", "live", "finished", "postponed", "cancelled"]


class FootballTeam(BaseModel):
    id: int | None = None
    name: str
    short_name: str = ""
    score: int | None = None
    logo_url: str = ""


class FootballVenue(BaseModel):
    name: str = ""
    city: str = ""
    country: str = ""


class FootballMatchPayload(BaseModel):
    match_id: int | None = None
    home: FootballTeam
    away: FootballTeam
    status: MatchStatus
    competition: str
    competition_id: int | None = None
    season: str = ""
    matchday: str | None = None
    venue: FootballVenue = FootballVenue()
    minute: int | None = None
    referee: str = ""
    match_date: str = ""


class StandingsEntry(BaseModel):
    position: int
    team: FootballTeam
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_diff: int
    points: int
    form: str = ""


class FootballStandingsPayload(BaseModel):
    competition: str
    competition_id: int | None = None
    season: str
    table: list[StandingsEntry]
