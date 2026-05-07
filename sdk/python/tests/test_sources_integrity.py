"""
CDS Integrity Brazil Test Suite
Tests for SanctionRecord, SanctionsConsolidated, parsing, summary, fetcher
(mocked), event signing, and an opt-in live integration test against the
real Portal da Transparência API.
"""
import json
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.signer import CDSSigner, CDSVerifier, generate_keypair
from cds.sources.integrity import (
    MissingTokenError,
    SanctionsFetcher,
    _build_sanctions_summary,
    _normalise_ceis,
    _normalise_cepim,
    _normalise_cnep,
    _parse_consolidated,
)
from cds.sources.integrity_models import IntegrityContentTypes
from cds.vocab import CDSSources, CDSVocab

# ── Fixtures ───────────────────────────────────────────────


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


# ── Sample upstream payloads ───────────────────────────────

CEIS_SANCTION_TYPE = (
    "Inidoneidade para licitar e contratar com a Administração Pública"
)

SAMPLE_CEIS_RECORD = {
    "id": 12345,
    "cnpjSancionado": "12345678000195",
    "nomeSancionado": "ACME LTDA",
    "razaoSocial": "ACME COMERCIO E SERVICOS LTDA",
    "tipoSancao": {"descricao": CEIS_SANCTION_TYPE},
    "dataInicioSancao": "2024-01-15",
    "dataFimSancao": "2026-01-15",
    "orgaoSancionador": {"nome": "Controladoria-Geral da União"},
    "fundamentacao": "Lei 8.666/93 art. 87 inc. IV",
    "informacoesAdicionais": "Processo administrativo nº ABC/2023",
}

SAMPLE_CNEP_RECORD = {
    "id": 67890,
    "cnpjSancionado": "12345678000195",
    "nomeSancionado": "ACME LTDA",
    "tipoSancao": {"descricao": "Multa"},
    "dataInicioSancao": "2023-06-01",
    "dataFimSancao": None,
    "orgaoSancionador": {"nome": "Ministério da Justiça"},
    "fundamentacao": "Lei 12.846/13 art. 6º",
}

SAMPLE_CEPIM_RECORD = {
    "id": 11111,
    "cnpjSancionado": "11222333000144",
    "nomeSancionado": "ASSOCIACAO BENEFICENTE EXEMPLO",
    "motivo": {"descricao": "Inadimplência na prestação de contas"},
    "dataInicio": "2023-09-10",
    "concedente": {"nome": "Ministério da Cidadania"},
}


# ── Content Type Tests ────────────────────────────────────


class TestIntegrityContentTypes:
    def test_all_are_uris(self):
        for ct in [
            IntegrityContentTypes.SANCTIONS_CONSOLIDATED,
            IntegrityContentTypes.SANCTIONS_CEIS,
            IntegrityContentTypes.SANCTIONS_CNEP,
            IntegrityContentTypes.SANCTIONS_CEPIM,
        ]:
            assert ct.startswith("https://signed-data.org/vocab/integrity-brazil/"), ct

    def test_consolidated_equals_vocab(self):
        assert (
            IntegrityContentTypes.SANCTIONS_CONSOLIDATED
            == CDSVocab.INTEGRITY_SANCTIONS_CONSOLIDATED
        )

    def test_consolidated_uri_value(self):
        assert IntegrityContentTypes.SANCTIONS_CONSOLIDATED == \
            "https://signed-data.org/vocab/integrity-brazil/sanctions-consolidated"

    def test_source_uri(self):
        assert CDSSources.PORTAL_TRANSPARENCIA == \
            "https://signed-data.org/sources/api.portaldatransparencia.gov.br.v1"


# ── Model Tests ───────────────────────────────────────────


class TestSanctionRecord:
    def test_preserves_raw_fields(self):
        record = _normalise_ceis(SAMPLE_CEIS_RECORD)
        # Normalised surface
        assert record.registry == "CEIS"
        assert record.cnpj == "12345678000195"
        assert record.nome_sancionado == "ACME LTDA"
        assert record.sanction_type == CEIS_SANCTION_TYPE
        assert record.start_date == "2024-01-15"
        assert record.end_date == "2026-01-15"
        assert record.sanctioning_organ == "Controladoria-Geral da União"
        assert record.legal_basis == "Lei 8.666/93 art. 87 inc. IV"
        # Verbatim raw is preserved untouched
        assert record.raw == SAMPLE_CEIS_RECORD
        assert record.raw["informacoesAdicionais"] == "Processo administrativo nº ABC/2023"
        assert record.raw["id"] == 12345

    def test_normalise_cnep(self):
        record = _normalise_cnep(SAMPLE_CNEP_RECORD)
        assert record.registry == "CNEP"
        assert record.sanction_type == "Multa"
        assert record.legal_basis == "Lei 12.846/13 art. 6º"
        assert record.end_date is None

    def test_normalise_cepim(self):
        record = _normalise_cepim(SAMPLE_CEPIM_RECORD)
        assert record.registry == "CEPIM"
        assert record.sanction_type == "Inadimplência na prestação de contas"
        assert record.start_date == "2023-09-10"
        assert record.sanctioning_organ == "Ministério da Cidadania"


class TestSanctionsConsolidatedModel:
    def test_clean_state(self):
        consolidated = _parse_consolidated(
            "33000167000101",
            "2026-04-07T14:30:00+00:00",
            ceis_raw=[],
            cnep_raw=[],
            cepim_raw=[],
        )
        assert consolidated.sanction_found is False
        assert consolidated.sanction_count == 0
        assert consolidated.is_clean is True
        assert consolidated.cnpj == "33000167000101"
        assert consolidated.cnpj_formatted == "33.000.167/0001-01"
        assert consolidated.registries == {"ceis": [], "cnep": [], "cepim": []}

    def test_sanctioned_state(self):
        consolidated = _parse_consolidated(
            "12345678000195",
            "2026-04-07T14:30:00+00:00",
            ceis_raw=[SAMPLE_CEIS_RECORD],
            cnep_raw=[SAMPLE_CNEP_RECORD],
            cepim_raw=[],
        )
        assert consolidated.sanction_found is True
        assert consolidated.sanction_count == 2
        assert consolidated.is_clean is False
        assert len(consolidated.registries["ceis"]) == 1
        assert len(consolidated.registries["cnep"]) == 1
        assert consolidated.registries["cepim"] == []
        assert consolidated.registries["ceis"][0].registry == "CEIS"
        assert consolidated.registries["cnep"][0].registry == "CNEP"


# ── Summary Tests ─────────────────────────────────────────


class TestSummary:
    def test_clean_summary(self):
        consolidated = _parse_consolidated(
            "33000167000101",
            "2026-04-07T14:30:00+00:00",
            ceis_raw=[],
            cnep_raw=[],
            cepim_raw=[],
        )
        summary = _build_sanctions_summary(consolidated)
        assert "33.000.167/0001-01" in summary
        assert "sem sanções" in summary
        assert "CEIS" in summary
        assert "CNEP" in summary
        assert "CEPIM" in summary

    def test_sanctioned_summary(self):
        consolidated = _parse_consolidated(
            "12345678000195",
            "2026-04-07T14:30:00+00:00",
            ceis_raw=[SAMPLE_CEIS_RECORD],
            cnep_raw=[SAMPLE_CNEP_RECORD],
            cepim_raw=[],
        )
        summary = _build_sanctions_summary(consolidated)
        assert "12.345.678/0001-95" in summary
        assert "2 sanç" in summary
        assert "1 em CEIS" in summary
        assert "1 em CNEP" in summary

    def test_single_sanction_summary(self):
        consolidated = _parse_consolidated(
            "12345678000195",
            "2026-04-07T14:30:00+00:00",
            ceis_raw=[SAMPLE_CEIS_RECORD],
            cnep_raw=[],
            cepim_raw=[],
        )
        summary = _build_sanctions_summary(consolidated)
        assert "1 sanç" in summary
        assert "1 em CEIS" in summary
        assert "CNEP" not in summary  # not in breakdown when count is 0


# ── Fetcher Tests (Mocked) ───────────────────────────────


def _make_mock_response(payload: list[dict]) -> MagicMock:
    """Build a mock httpx.Response that returns `payload` as JSON."""
    body = json.dumps(payload).encode("utf-8")
    resp = MagicMock()
    resp.content = body
    resp.json.return_value = payload
    resp.raise_for_status = MagicMock()
    return resp


class TestSanctionsFetcherInit:
    def test_missing_token_raises(self):
        with pytest.raises(MissingTokenError, match="token is required"):
            SanctionsFetcher(token="")

    def test_with_token(self):
        fetcher = SanctionsFetcher(token="test-token")
        assert fetcher.token == "test-token"
        assert fetcher.signer is None


class TestSanctionsFetcherClean:
    @pytest.mark.asyncio
    async def test_fetch_consolidated_clean(self):
        with patch("cds.sources.integrity.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=[
                _make_mock_response([]),  # CEIS empty
                _make_mock_response([]),  # CNEP empty
                _make_mock_response([]),  # CEPIM empty
            ])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            fetcher = SanctionsFetcher(token="test-token")
            event = await fetcher.fetch_consolidated("33.000.167/0001-01")

            assert event.content_type == IntegrityContentTypes.SANCTIONS_CONSOLIDATED
            assert event.payload["sanction_found"] is False
            assert event.payload["sanction_count"] == 0
            assert event.payload["cnpj"] == "33000167000101"
            assert event.domain == "integrity.brazil"
            assert event.event_type == "sanctions.consolidated"
            assert "sem sanções" in event.event_context.summary


class TestSanctionsFetcherSanctioned:
    @pytest.mark.asyncio
    async def test_fetch_consolidated_sanctioned(self):
        with patch("cds.sources.integrity.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=[
                _make_mock_response([SAMPLE_CEIS_RECORD]),
                _make_mock_response([SAMPLE_CNEP_RECORD]),
                _make_mock_response([]),
            ])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            fetcher = SanctionsFetcher(token="test-token")
            event = await fetcher.fetch_consolidated("12345678000195")

            assert event.payload["sanction_found"] is True
            assert event.payload["sanction_count"] == 2
            assert len(event.payload["registries"]["ceis"]) == 1
            assert len(event.payload["registries"]["cnep"]) == 1
            assert event.payload["registries"]["cepim"] == []
            # Verify raw verbatim record survived round-trip through model_dump
            ceis0 = event.payload["registries"]["ceis"][0]
            assert ceis0["raw"]["informacoesAdicionais"] == "Processo administrativo nº ABC/2023"

    @pytest.mark.asyncio
    async def test_invalid_cnpj_raises(self):
        fetcher = SanctionsFetcher(token="test-token")
        with pytest.raises(ValueError, match="check digit"):
            await fetcher.fetch_consolidated("11222333000199")


# ── Event signing tests ──────────────────────────────────


class TestSanctionsEvent:
    def test_signing_and_verification(self, signer, verifier):
        event = CDSEvent(
            content_type=IntegrityContentTypes.SANCTIONS_CONSOLIDATED,
            source=SourceMeta(id=CDSSources.PORTAL_TRANSPARENCIA, fingerprint="sha256:mock"),
            occurred_at=datetime(2026, 4, 7, tzinfo=UTC),
            lang="pt-BR",
            payload={
                "cnpj": "33000167000101",
                "cnpj_formatted": "33.000.167/0001-01",
                "sanction_found": False,
                "sanction_count": 0,
                "registries": {"ceis": [], "cnep": [], "cepim": []},
                "query_timestamp": "2026-04-07T14:30:00+00:00",
            },
            event_context=ContextMeta(
                summary="33.000.167/0001-01: sem sanções federais.",
                model="rule-based-v1",
            ),
        )
        signer.sign(event)
        assert verifier.verify(event) is True

    def test_jsonld_fields(self):
        event = CDSEvent(
            content_type=IntegrityContentTypes.SANCTIONS_CONSOLIDATED,
            source=SourceMeta(id=CDSSources.PORTAL_TRANSPARENCIA),
            occurred_at=datetime(2026, 4, 7, tzinfo=UTC),
            lang="pt-BR",
            payload={"cnpj": "33000167000101", "sanction_found": False},
        )
        d = event.to_jsonld()
        assert d["content_type"].startswith("https://signed-data.org/vocab/integrity-brazil/")
        assert d["source"]["@id"] == "https://signed-data.org/sources/api.portaldatransparencia.gov.br.v1"
        assert d["@type"] == "https://signed-data.org/vocab/CuratedDataEvent"


# ── Live integration test (opt-in) ───────────────────────


@pytest.mark.skipif(
    not os.environ.get("PORTAL_TRANSPARENCIA_TOKEN"),
    reason="Set PORTAL_TRANSPARENCIA_TOKEN to enable live integration test",
)
class TestLiveIntegration:
    """Hits the real Portal da Transparência API. Skipped unless
    PORTAL_TRANSPARENCIA_TOKEN is set.

    Counts against the API rate limit (90 req/min in business hours; one
    test = 3 requests). Run sparingly.
    """

    @pytest.mark.asyncio
    async def test_check_clean_cnpj_banco_brasil(self):
        """BANCO DO BRASIL S.A. — large, public, expected to be clean."""
        token = os.environ["PORTAL_TRANSPARENCIA_TOKEN"]
        fetcher = SanctionsFetcher(token=token)
        try:
            event = await fetcher.fetch_consolidated("00000000000191")
        except httpx.HTTPStatusError as exc:
            pytest.skip(f"Portal da Transparência upstream error: {exc.response.status_code}")

        assert event.content_type == IntegrityContentTypes.SANCTIONS_CONSOLIDATED
        assert event.payload["cnpj"] == "00000000000191"
        # We assert the call works, not the specific finding — the live state
        # of the registry can change.
        assert "sanction_found" in event.payload
        assert "sanction_count" in event.payload
        assert isinstance(event.payload["sanction_count"], int)
        assert set(event.payload["registries"].keys()) == {"ceis", "cnep", "cepim"}

    @pytest.mark.asyncio
    async def test_check_petrobras(self):
        """PETROBRAS — also large, public, used as a CNPJ-format canary."""
        token = os.environ["PORTAL_TRANSPARENCIA_TOKEN"]
        fetcher = SanctionsFetcher(token=token)
        try:
            event = await fetcher.fetch_consolidated("33.000.167/0001-01")
        except httpx.HTTPStatusError as exc:
            pytest.skip(f"Portal da Transparência upstream error: {exc.response.status_code}")

        assert event.payload["cnpj"] == "33000167000101"
        assert event.payload["cnpj_formatted"] == "33.000.167/0001-01"
        # Signature should NOT be applied (no signer was provided)
        assert event.integrity is None
