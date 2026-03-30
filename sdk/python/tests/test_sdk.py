"""
SignedData CDS — Python SDK Test Suite
"""
import json
import pytest
from datetime import datetime, timezone

from cds.schema import CDSEvent, CDSContentType, SourceMeta, ContextMeta
from cds.signer import CDSSigner, CDSVerifier, generate_keypair
from cds.sources.football_models import (
    FootballContentTypes, FootballMatchPayload,
    FootballTeam, FootballVenue,
)


@pytest.fixture(scope="session")
def keypair(tmp_path_factory):
    d    = tmp_path_factory.mktemp("keys")
    priv = str(d / "private.pem")
    pub  = str(d / "public.pem")
    generate_keypair(priv, pub)
    return priv, pub


@pytest.fixture
def signer(keypair):
    return CDSSigner(keypair[0], issuer="test.signed-data.org")


@pytest.fixture
def verifier(keypair):
    return CDSVerifier(keypair[1])


@pytest.fixture
def football_event(signer):
    payload = FootballMatchPayload(
        home=FootballTeam(name="Flamengo",   short_name="FLA", score=2, logo_url=""),
        away=FootballTeam(name="Fluminense", short_name="FLU", score=1, logo_url=""),
        status="finished",
        competition="Brasileirão Série A",
        season="2026",
        venue=FootballVenue(),
        referee="",
        match_date="2026-03-22",
    )
    event = CDSEvent(
        content_type=FootballContentTypes.MATCH_RESULT,
        source=SourceMeta(id="api-football.com.v3", fingerprint="sha256:abc"),
        occurred_at=datetime(2026, 3, 22, 21, 0, tzinfo=timezone.utc),
        lang="en",
        payload=payload.model_dump(mode="json"),
        context=ContextMeta(summary="Flamengo 2 x 1 Fluminense", model="rule-based-v1"),
    )
    return signer.sign(event)


# ── CDSContentType ─────────────────────────────────────────

class TestCDSContentType:
    def test_mime_weather(self):
        ct = CDSContentType(domain="weather", schema_name="forecast.current")
        assert ct.mime_type == "application/vnd.cds.weather.forecast-current+json;v=1"

    def test_mime_football(self):
        assert FootballContentTypes.MATCH_RESULT.mime_type == \
            "application/vnd.cds.sports-football.match-result+json;v=1"

    def test_domain_property(self):
        ct = CDSContentType(domain="news", schema_name="headline")
        assert ct.domain == "news" and ct.schema_name == "headline"


# ── CDSEvent ───────────────────────────────────────────────

class TestCDSEvent:
    def test_canonical_deterministic(self, football_event):
        assert football_event.canonical_bytes() == football_event.canonical_bytes()

    def test_canonical_excludes_integrity(self, football_event):
        parsed = json.loads(football_event.canonical_bytes())
        assert "integrity"  not in parsed
        assert "ingested_at" not in parsed

    def test_domain_shortcut(self, football_event):
        assert football_event.domain     == "sports.football"
        assert football_event.event_type == "match.result"


# ── Signer ─────────────────────────────────────────────────

class TestCDSSigner:
    def test_integrity_attached(self, football_event):
        i = football_event.integrity
        assert i is not None
        assert i.hash.startswith("sha256:")
        assert i.signed_by == "test.signed-data.org"
        assert len(i.signature) > 0

    def test_hash_correct(self, football_event):
        import hashlib
        expected = "sha256:" + hashlib.sha256(football_event.canonical_bytes()).hexdigest()
        assert football_event.integrity.hash == expected


# ── Verifier ───────────────────────────────────────────────

class TestCDSVerifier:
    def test_valid(self, verifier, football_event):
        assert verifier.verify(football_event) is True

    def test_tampered_score(self, verifier, football_event):
        raw = json.loads(football_event.model_dump_json())
        t   = CDSEvent(**raw)
        t.payload["home"]["score"] = 99
        with pytest.raises(Exception):
            verifier.verify(t)

    def test_tampered_summary(self, verifier, football_event):
        raw = json.loads(football_event.model_dump_json())
        t   = CDSEvent(**raw)
        t.context.summary = "tampered"  # type: ignore[union-attr]
        with pytest.raises(Exception):
            verifier.verify(t)

    def test_no_integrity(self, verifier):
        e = CDSEvent(
            content_type=CDSContentType(domain="news", schema_name="headline"),
            source=SourceMeta(id="test"),
            occurred_at=datetime.now(timezone.utc),
            payload={"title": "Test"},
        )
        with pytest.raises(ValueError, match="no integrity"):
            verifier.verify(e)

    def test_roundtrip(self, verifier, football_event):
        raw      = json.loads(football_event.model_dump_json())
        restored = CDSEvent(**raw)
        assert verifier.verify(restored) is True


# ── Football models ────────────────────────────────────────

class TestFootballModels:
    def test_content_types(self):
        assert FootballContentTypes.MATCH_RESULT.domain == "sports.football"
        assert FootballContentTypes.MATCH_LIVE.schema_name == "match.live"

    def test_payload_roundtrip(self, football_event):
        p = FootballMatchPayload(**football_event.payload)
        assert p.home.name == "Flamengo"
        assert p.home.score == 2
        assert p.status == "finished"
