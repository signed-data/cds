"""
CDS SDK Test Suite v0.2.0
25 tests across: CDSVocab, SourceMeta, CDSEvent, canonical bytes,
signing/verification, domain models.
"""
import hashlib
import json
from datetime import UTC, datetime

import pytest

from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.signer import CDSSigner, CDSVerifier, generate_keypair
from cds.sources.football_models import FootballContentTypes
from cds.sources.lottery_models import LotteryContentTypes, MegaSenaResult
from cds.vocab import (
    CONTEXT_URI,
    EVENT_TYPE_URI,
    CDSSources,
    CDSVocab,
    content_type_uri,
    source_uri,
)

# ── Fixtures ───────────────────────────────────────────────

@pytest.fixture(scope="session")
def keypair(tmp_path_factory):
    d    = tmp_path_factory.mktemp("keys")
    priv = str(d / "private.pem")
    pub  = str(d / "public.pem")
    generate_keypair(priv, pub)
    return priv, pub


@pytest.fixture(scope="session")
def signer(keypair):
    return CDSSigner(keypair[0], issuer="https://signed-data.org")


@pytest.fixture(scope="session")
def verifier(keypair):
    return CDSVerifier(keypair[1])


@pytest.fixture
def lottery_event():
    return CDSEvent(
        content_type  = CDSVocab.LOTTERY_MEGA_SENA,
        source        = SourceMeta(id=CDSSources.CAIXA_LOTERIAS, fingerprint="sha256:mock"),
        occurred_at   = datetime(2026, 3, 29, tzinfo=UTC),
        lang          = "pt-BR",
        payload       = {"concurso": 2800, "dezenas": ["04","12","25","36","47","59"]},
        event_context = ContextMeta(summary="Mega Sena 2800", model="rule-based-v1"),
    )


@pytest.fixture
def football_event():
    return CDSEvent(
        content_type  = CDSVocab.FOOTBALL_MATCH_RESULT,
        source        = SourceMeta(id=CDSSources.API_FOOTBALL, fingerprint="sha256:mock"),
        occurred_at   = datetime(2026, 3, 22, 21, tzinfo=UTC),
        lang          = "pt-BR",
        payload       = {"home": {"name": "Flamengo", "score": 2},
                         "away": {"name": "Fluminense", "score": 1}},
        event_context = ContextMeta(summary="Flamengo 2-1 Fluminense"),
    )


# ── CDSVocab ───────────────────────────────────────────────

class TestCDSVocab:
    def test_lottery_mega_sena_uri(self):
        assert CDSVocab.LOTTERY_MEGA_SENA == \
            "https://signed-data.org/vocab/lottery-brazil/mega-sena-result"

    def test_football_match_result_uri(self):
        assert CDSVocab.FOOTBALL_MATCH_RESULT == \
            "https://signed-data.org/vocab/sports-football/match-result"

    def test_weather_current_uri(self):
        assert CDSVocab.WEATHER_CURRENT == \
            "https://signed-data.org/vocab/weather/forecast-current"

    def test_content_type_uri_builder(self):
        assert content_type_uri("lottery.brazil", "mega-sena.result") == \
            "https://signed-data.org/vocab/lottery-brazil/mega-sena-result"

    def test_source_uri_keeps_dots(self):
        assert source_uri("caixa.gov.br.loterias.v1") == \
            "https://signed-data.org/sources/caixa.gov.br.loterias.v1"


# ── SourceMeta ─────────────────────────────────────────────

class TestSourceMeta:
    def test_id_field_access(self):
        s = SourceMeta(id=CDSSources.CAIXA_LOTERIAS)
        assert s.id == "https://signed-data.org/sources/caixa.gov.br.loterias.v1"

    def test_alias_constructor(self):
        s = SourceMeta(**{"@id": CDSSources.CAIXA_LOTERIAS})
        assert s.id == CDSSources.CAIXA_LOTERIAS

    def test_serialises_with_at_id(self):
        d = SourceMeta(id=CDSSources.CAIXA_LOTERIAS, fingerprint="sha256:abc") \
            .model_dump(by_alias=True)
        assert "@id" in d
        assert "id"  not in d


# ── CDSEvent ───────────────────────────────────────────────

class TestCDSEventConstruction:
    def test_at_context(self, lottery_event):
        assert lottery_event.ld_context == CONTEXT_URI

    def test_at_type(self, lottery_event):
        assert lottery_event.ld_type == EVENT_TYPE_URI

    def test_at_id_auto_set(self, lottery_event):
        assert lottery_event.ld_id == \
            f"https://signed-data.org/events/{lottery_event.id}"

    def test_content_type_is_uri(self, lottery_event):
        assert lottery_event.content_type.startswith("https://signed-data.org/vocab/")

    def test_source_id_is_uri(self, lottery_event):
        assert lottery_event.source.id.startswith("https://signed-data.org/sources/")

    def test_spec_version(self, lottery_event):
        assert lottery_event.spec_version == "0.2.0"

    def test_domain_shortcut(self, lottery_event):
        assert lottery_event.domain == "lottery.brazil"

    def test_event_type_shortcut(self, lottery_event):
        assert lottery_event.event_type == "mega-sena.result"

    def test_football_shortcuts(self, football_event):
        assert football_event.domain     == "sports.football"
        assert football_event.event_type == "match.result"


# ── Serialisation ──────────────────────────────────────────

class TestSerialisation:
    def test_at_fields_present(self, lottery_event):
        d = lottery_event.to_jsonld()
        assert "@context" in d
        assert "@type"    in d
        assert "@id"      in d

    def test_at_fields_first(self, lottery_event):
        keys = list(lottery_event.to_jsonld().keys())
        assert keys[:3] == ["@context", "@type", "@id"]

    def test_source_serialises_at_id(self, lottery_event):
        d = lottery_event.to_jsonld()
        assert "@id" in d["source"]
        assert "id"  not in d["source"]

    def test_json_roundtrip(self, lottery_event):
        raw      = json.dumps(lottery_event.to_jsonld())
        restored = CDSEvent.from_jsonld(json.loads(raw))
        assert restored.id           == lottery_event.id
        assert restored.content_type == lottery_event.content_type


# ── Canonical bytes ────────────────────────────────────────

class TestCanonicalBytes:
    def test_includes_at_fields(self, lottery_event):
        d = json.loads(lottery_event.canonical_bytes())
        assert "@context" in d
        assert "@type"    in d
        assert "@id"      in d

    def test_excludes_integrity(self, lottery_event, signer):
        signer.sign(lottery_event)
        d = json.loads(lottery_event.canonical_bytes())
        assert "integrity" not in d

    def test_excludes_ingested_at(self, lottery_event):
        d = json.loads(lottery_event.canonical_bytes())
        assert "ingested_at" not in d

    def test_is_deterministic(self, lottery_event):
        assert lottery_event.canonical_bytes() == lottery_event.canonical_bytes()

    def test_keys_are_sorted(self, lottery_event):
        keys = list(json.loads(lottery_event.canonical_bytes()).keys())
        assert keys == sorted(keys)


# ── Signing and verification ───────────────────────────────

class TestSigning:
    def test_sign_attaches_integrity(self, lottery_event, signer):
        signer.sign(lottery_event)
        assert lottery_event.integrity is not None

    def test_signed_by_is_uri(self, lottery_event, signer):
        signer.sign(lottery_event)
        assert lottery_event.integrity.signed_by == "https://signed-data.org"

    def test_hash_matches_canonical(self, lottery_event, signer):
        signer.sign(lottery_event)
        expected = "sha256:" + hashlib.sha256(lottery_event.canonical_bytes()).hexdigest()
        assert lottery_event.integrity.hash == expected

    def test_verify_valid(self, lottery_event, signer, verifier):
        signer.sign(lottery_event)
        assert verifier.verify(lottery_event) is True

    def test_tamper_payload_fails(self, lottery_event, signer, verifier):
        signer.sign(lottery_event)
        lottery_event.payload["concurso"] = 9999
        with pytest.raises(ValueError):
            verifier.verify(lottery_event)

    def test_tamper_summary_fails(self, football_event, signer, verifier):
        signer.sign(football_event)
        football_event.event_context.summary = "tampered"
        with pytest.raises(ValueError):
            verifier.verify(football_event)

    def test_no_integrity_raises(self, football_event, verifier):
        with pytest.raises(ValueError, match="no integrity"):
            verifier.verify(football_event)

    def test_verify_after_roundtrip(self, football_event, signer, verifier):
        signer.sign(football_event)
        restored = CDSEvent.from_jsonld(json.loads(json.dumps(football_event.to_jsonld())))
        assert verifier.verify(restored) is True


# ── Domain models ──────────────────────────────────────────

class TestLotteryModels:
    def test_content_types_are_uris(self):
        for ct in [LotteryContentTypes.MEGA_SENA, LotteryContentTypes.LOTOFACIL,
                   LotteryContentTypes.QUINA, LotteryContentTypes.LOTOMANIA,
                   LotteryContentTypes.DUPLA_SENA]:
            assert ct.startswith("https://"), ct

    def test_mega_sena_equals_vocab(self):
        assert LotteryContentTypes.MEGA_SENA == CDSVocab.LOTTERY_MEGA_SENA

    def test_mega_sena_result_model(self):
        r = MegaSenaResult(
            concurso=2800, data_apuracao="29/03/2026",
            data_apuracao_iso="2026-03-29",
            dezenas=["04","12","25","36","47","59"], acumulado=False,
        )
        assert r.dezenas_formatted == "04 \u00b7 12 \u00b7 25 \u00b7 36 \u00b7 47 \u00b7 59"


class TestFootballModels:
    def test_content_types_are_uris(self):
        assert FootballContentTypes.MATCH_RESULT.startswith("https://")

    def test_match_result_equals_vocab(self):
        assert FootballContentTypes.MATCH_RESULT == CDSVocab.FOOTBALL_MATCH_RESULT
