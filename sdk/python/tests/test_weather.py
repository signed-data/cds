"""CDS Weather Test Suite — WeatherIngestor, content types, signing."""
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.signer import CDSSigner, CDSVerifier, generate_keypair
from cds.sources.weather import WeatherIngestor
from cds.vocab import CDSSources, CDSVocab

MOCK_OPEN_METEO_RESPONSE = {
    "latitude": -23.5505,
    "longitude": -46.6333,
    "current_weather": {
        "temperature": 22.5,
        "windspeed": 12.3,
        "winddirection": 180,
        "weathercode": 3,
        "time": "2026-04-20T12:00",
    },
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


class TestWeatherVocab:
    def test_current_uri(self):
        assert CDSVocab.WEATHER_CURRENT == "https://signed-data.org/vocab/weather/forecast-current"

    def test_daily_uri(self):
        assert CDSVocab.WEATHER_DAILY == "https://signed-data.org/vocab/weather/forecast-daily"

    def test_alert_uri(self):
        assert CDSVocab.WEATHER_ALERT == "https://signed-data.org/vocab/weather/alert-severe"

    def test_open_meteo_source_uri(self):
        assert CDSSources.OPEN_METEO.startswith("https://signed-data.org/sources/")


class TestWeatherIngestor:
    def _mock_client(self, resp):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        return mock_client

    def _mock_response(self, data):
        r = MagicMock()
        r.content = json.dumps(data).encode()
        r.json.return_value = data
        r.raise_for_status = MagicMock()
        return r

    @pytest.mark.asyncio
    async def test_fetch_returns_one_event(self):
        mock_resp = self._mock_response(MOCK_OPEN_METEO_RESPONSE)
        with patch("cds.sources.weather.httpx.AsyncClient") as cls:
            cls.return_value = self._mock_client(mock_resp)
            events = await WeatherIngestor(signer=None).fetch()
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_content_type(self):
        mock_resp = self._mock_response(MOCK_OPEN_METEO_RESPONSE)
        with patch("cds.sources.weather.httpx.AsyncClient") as cls:
            cls.return_value = self._mock_client(mock_resp)
            events = await WeatherIngestor(signer=None).fetch()
        assert events[0].content_type == CDSVocab.WEATHER_CURRENT

    @pytest.mark.asyncio
    async def test_payload_fields(self):
        mock_resp = self._mock_response(MOCK_OPEN_METEO_RESPONSE)
        with patch("cds.sources.weather.httpx.AsyncClient") as cls:
            cls.return_value = self._mock_client(mock_resp)
            events = await WeatherIngestor(signer=None).fetch()
        p = events[0].payload
        assert p["location"] == "São Paulo, BR"
        assert p["temperature"] == 22.5
        assert p["windspeed"] == 12.3

    @pytest.mark.asyncio
    async def test_unsigned_on_fetch(self):
        mock_resp = self._mock_response(MOCK_OPEN_METEO_RESPONSE)
        with patch("cds.sources.weather.httpx.AsyncClient") as cls:
            cls.return_value = self._mock_client(mock_resp)
            events = await WeatherIngestor(signer=None).fetch()
        assert events[0].integrity is None

    @pytest.mark.asyncio
    async def test_ingest_signs_event(self, signer, verifier):
        mock_resp = self._mock_response(MOCK_OPEN_METEO_RESPONSE)
        with patch("cds.sources.weather.httpx.AsyncClient") as cls:
            cls.return_value = self._mock_client(mock_resp)
            events = await WeatherIngestor(signer=signer).ingest()
        assert events[0].integrity is not None
        assert verifier.verify(events[0])

    @pytest.mark.asyncio
    async def test_custom_location(self):
        mock_resp = self._mock_response(MOCK_OPEN_METEO_RESPONSE)
        with patch("cds.sources.weather.httpx.AsyncClient") as cls:
            cls.return_value = self._mock_client(mock_resp)
            events = await WeatherIngestor(
                signer=None,
                latitude=-23.1854,
                longitude=-46.8978,
                location_name="Jundiaí, BR",
            ).fetch()
        assert events[0].payload["location"] == "Jundiaí, BR"
        assert events[0].payload["latitude"] == -23.1854

    def test_event_domain(self):
        event = CDSEvent(
            content_type=CDSVocab.WEATHER_CURRENT,
            source=SourceMeta(id=CDSSources.OPEN_METEO, fingerprint="sha256:mock"),
            occurred_at=datetime(2026, 4, 20, tzinfo=UTC),
            lang="en",
            payload={"location": "São Paulo", "temperature": 22.5},
        )
        assert event.domain == "weather"
        assert event.event_type == "forecast.current"

    def test_event_jsonld(self):
        event = CDSEvent(
            content_type=CDSVocab.WEATHER_CURRENT,
            source=SourceMeta(id=CDSSources.OPEN_METEO),
            occurred_at=datetime(2026, 4, 20, tzinfo=UTC),
            lang="en",
            payload={"location": "São Paulo"},
        )
        d = event.to_jsonld()
        assert d["content_type"].startswith("https://signed-data.org/vocab/")
        assert d["source"]["@id"].startswith("https://signed-data.org/sources/")

    def test_summary_includes_location(self):
        mock_resp = MagicMock()
        mock_resp.content = json.dumps(MOCK_OPEN_METEO_RESPONSE).encode()
        mock_resp.json.return_value = MOCK_OPEN_METEO_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        import asyncio
        with patch("cds.sources.weather.httpx.AsyncClient") as cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            cls.return_value = mock_client
            events = asyncio.run(
                WeatherIngestor(signer=None).fetch()
            )
        assert "São Paulo" in events[0].event_context.summary


class TestWeatherServerTools:
    def test_three_tools_in_server_file(self):
        from pathlib import Path
        server_path = Path(__file__).parent.parent.parent.parent / "mcp/weather/server.py"
        source = server_path.read_text()
        for tool in ["get_current_weather", "get_daily_forecast", "list_weather_locations"]:
            assert f"async def {tool}" in source, f"Missing tool: {tool}"
