"""CDS Sports Football Test Suite — FootballIngestor, models, content types, signing."""
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.signer import CDSSigner, CDSVerifier, generate_keypair
from cds.sources.football import LEAGUE_IDS, FootballIngestor
from cds.sources.football_models import (
    FootballContentTypes,
    FootballMatchPayload,
    FootballStandingsPayload,
    FootballTeam,
    FootballVenue,
    StandingsEntry,
)
from cds.vocab import CDSSources, CDSVocab

MOCK_FIXTURE_FINISHED = {
    "response": [
        {
            "fixture": {
                "id": 1001,
                "date": "2026-04-20T20:00:00+00:00",
                "status": {"short": "FT", "elapsed": 90},
                "referee": "Referee X",
                "venue": {"name": "Allianz Parque", "city": "São Paulo"},
            },
            "teams": {
                "home": {"id": 121, "name": "Palmeiras", "logo": ""},
                "away": {"id": 128, "name": "Flamengo", "logo": ""},
            },
            "goals": {"home": 2, "away": 1},
            "league": {
                "id": 71, "name": "Brasileirão Série A",
                "season": 2026, "round": "Regular Season - 5",
            },
        }
    ]
}

MOCK_FIXTURE_LIVE = {
    "response": [
        {
            "fixture": {
                "id": 1002,
                "date": "2026-04-20T21:00:00+00:00",
                "status": {"short": "1H", "elapsed": 35},
                "referee": "",
                "venue": {},
            },
            "teams": {
                "home": {"id": 1, "name": "Team A", "logo": ""},
                "away": {"id": 2, "name": "Team B", "logo": ""},
            },
            "goals": {"home": 1, "away": 0},
            "league": {
                "id": 71, "name": "Brasileirão Série A",
                "season": 2026, "round": "Regular Season - 6",
            },
        }
    ]
}


@pytest.fixture(scope="session")
def keypair(tmp_path_factory):
    d = tmp_path_factory.mktemp("keys")
    priv = str(d / "private.pem")
    pub = str(d / "public.pem")
    generate_keypair(priv, pub)
    return priv, pub


@pytest.fixture(scope="session")
def signer(keypair):
    return CDSSigner(keypair[0], issuer="https://signed-data.org")


@pytest.fixture(scope="session")
def verifier(keypair):
    return CDSVerifier(keypair[1])


class TestFootballVocab:
    def test_match_result_uri(self):
        assert CDSVocab.FOOTBALL_MATCH_RESULT == "https://signed-data.org/vocab/sports-football/match-result"

    def test_match_live_uri(self):
        assert CDSVocab.FOOTBALL_MATCH_LIVE == "https://signed-data.org/vocab/sports-football/match-live"

    def test_standings_uri(self):
        assert CDSVocab.FOOTBALL_STANDINGS == "https://signed-data.org/vocab/sports-football/standings-update"

    def test_api_football_source_uri(self):
        assert CDSSources.API_FOOTBALL.startswith("https://signed-data.org/sources/")


class TestLeagueIds:
    def test_brasileirao_a(self):
        assert LEAGUE_IDS["brasileirao_a"] == 71

    def test_premier_league(self):
        assert LEAGUE_IDS["premier_league"] == 39

    def test_champions_league(self):
        assert LEAGUE_IDS["champions_league"] == 2

    def test_all_keys_present(self):
        expected = {"brasileirao_a", "brasileirao_b", "copa_brasil", "libertadores",
                    "sul_americana", "premier_league", "champions_league"}
        assert set(LEAGUE_IDS.keys()) == expected


class TestFootballModels:
    def test_match_payload(self):
        p = FootballMatchPayload(
            match_id=1001,
            home=FootballTeam(id=121, name="Palmeiras", short_name="PAL", score=2),
            away=FootballTeam(id=128, name="Flamengo", short_name="FLA", score=1),
            status="finished",
            competition="Brasileirão Série A",
            match_date="2026-04-20",
        )
        assert p.home.score == 2
        assert p.status == "finished"

    def test_standings_payload(self):
        entry = StandingsEntry(
            position=1,
            team=FootballTeam(id=121, name="Palmeiras", short_name="PAL"),
            played=5, won=4, drawn=1, lost=0,
            goals_for=12, goals_against=3, goal_diff=9, points=13,
        )
        table = FootballStandingsPayload(
            competition="Brasileirão", competition_id=71, season="2026", table=[entry],
        )
        assert table.table[0].points == 13


class TestFootballIngestor:
    def _mock_client(self, resp):
        mc = AsyncMock()
        mc.get = AsyncMock(return_value=resp)
        mc.__aenter__ = AsyncMock(return_value=mc)
        mc.__aexit__ = AsyncMock(return_value=False)
        return mc

    def _mock_response(self, data):
        r = MagicMock()
        r.content = json.dumps(data).encode()
        r.json.return_value = data
        r.raise_for_status = MagicMock()
        return r

    @pytest.mark.asyncio
    async def test_fetch_finished_match(self):
        with patch("cds.sources.football.httpx.AsyncClient") as cls:
            cls.return_value = self._mock_client(self._mock_response(MOCK_FIXTURE_FINISHED))
            events = await FootballIngestor(signer=None, api_key="test").fetch()
        assert len(events) == 1
        assert events[0].content_type == FootballContentTypes.MATCH_RESULT
        assert events[0].payload["home"]["name"] == "Palmeiras"
        assert events[0].payload["status"] == "finished"

    @pytest.mark.asyncio
    async def test_fetch_live_match_content_type(self):
        with patch("cds.sources.football.httpx.AsyncClient") as cls:
            cls.return_value = self._mock_client(self._mock_response(MOCK_FIXTURE_LIVE))
            events = await FootballIngestor(signer=None, api_key="test").fetch()
        assert events[0].content_type == FootballContentTypes.MATCH_LIVE
        assert events[0].payload["status"] == "live"

    @pytest.mark.asyncio
    async def test_ingest_signs_event(self, signer, verifier):
        with patch("cds.sources.football.httpx.AsyncClient") as cls:
            cls.return_value = self._mock_client(self._mock_response(MOCK_FIXTURE_FINISHED))
            events = await FootballIngestor(signer=signer, api_key="test").ingest()
        assert events[0].integrity is not None
        assert verifier.verify(events[0])

    @pytest.mark.asyncio
    async def test_score_parsed(self):
        with patch("cds.sources.football.httpx.AsyncClient") as cls:
            cls.return_value = self._mock_client(self._mock_response(MOCK_FIXTURE_FINISHED))
            events = await FootballIngestor(signer=None, api_key="test").fetch()
        assert events[0].payload["home"]["score"] == 2
        assert events[0].payload["away"]["score"] == 1

    def test_event_domain(self):
        event = CDSEvent(
            content_type=FootballContentTypes.MATCH_RESULT,
            source=SourceMeta(id=CDSSources.API_FOOTBALL, fingerprint="sha256:mock"),
            occurred_at=datetime(2026, 4, 20, tzinfo=UTC),
            lang="en",
            payload={"home": {}, "away": {}, "status": "finished"},
        )
        assert event.domain == "sports.football"
        assert event.event_type == "match.result"

    def test_event_jsonld(self):
        event = CDSEvent(
            content_type=FootballContentTypes.MATCH_RESULT,
            source=SourceMeta(id=CDSSources.API_FOOTBALL),
            occurred_at=datetime(2026, 4, 20, tzinfo=UTC),
            lang="en",
            payload={"home": {}, "away": {}, "status": "finished"},
        )
        d = event.to_jsonld()
        assert d["content_type"].startswith("https://signed-data.org/vocab/")


class TestSportsServerTools:
    def test_four_tools_in_server_file(self):
        from pathlib import Path
        server_path = Path(__file__).parent.parent.parent.parent / "mcp/sports/server.py"
        source = server_path.read_text()
        for tool in ["get_match_results", "get_live_scores", "get_standings", "list_leagues"]:
            assert f"async def {tool}" in source, f"Missing tool: {tool}"
