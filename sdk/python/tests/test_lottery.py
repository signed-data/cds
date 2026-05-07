"""
CDS Lottery Brazil Test Suite (lottery.brazil)
Tests for MegaSenaResult parsing, build_summary, MegaSenaIngestor (mocked),
event signing, and the MCP server tool definitions.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cds.signer import CDSSigner, CDSVerifier, generate_keypair
from cds.sources.lottery import (
    MegaSenaIngestor,
    _build_summary,
    _parse_response,
)
from cds.sources.lottery_models import (
    LotteryContentTypes,
)
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


# ── Sample upstream payload ────────────────────────────────

SAMPLE_CAIXA_RESPONSE = {
    "numero": 2850,
    "dataApuracao": "05/04/2026",
    "listaDezenas": ["04", "15", "22", "37", "51", "58"],
    "listaDezenasOrdemSorteio": ["22", "04", "51", "15", "58", "37"],
    "acumulado": False,
    "localSorteio": "Espaço Loterias Caixa",
    "nomeMunicipiUFSorteio": "SÃO PAULO, SP",
    "listaRateioPremio": [
        {
            "descricao": "Sena",
            "numeroDeGanhadores": 2,
            "valorPremio": 45_000_000.0,
        },
        {
            "descricao": "Quina",
            "numeroDeGanhadores": 120,
            "valorPremio": 35_800.0,
        },
        {
            "descricao": "Quadra",
            "numeroDeGanhadores": 8_400,
            "valorPremio": 680.0,
        },
    ],
    "valorArrecadado": 98_000_000.0,
    "valorEstimadoProximoConcurso": 3_000_000.0,
    "dataProximoConcurso": "08/04/2026",
    "numeroConcursoAnterior": 2849,
    "numeroConcursoProximo": 2851,
}

SAMPLE_ACUMULADO_RESPONSE = {
    **SAMPLE_CAIXA_RESPONSE,
    "acumulado": True,
    "listaRateioPremio": [
        {
            "descricao": "Sena",
            "numeroDeGanhadores": 0,
            "valorPremio": 0.0,
        },
    ],
    "valorEstimadoProximoConcurso": 120_000_000.0,
    "dataProximoConcurso": "08/04/2026",
}


# ── Parsing tests ──────────────────────────────────────────


class TestParseResponse:
    def test_concurso_number(self):
        result = _parse_response(SAMPLE_CAIXA_RESPONSE)
        assert result.concurso == 2850

    def test_dezenas_sorted(self):
        result = _parse_response(SAMPLE_CAIXA_RESPONSE)
        assert result.dezenas == ["04", "15", "22", "37", "51", "58"]

    def test_dezenas_sorted_ascending(self):
        result = _parse_response(SAMPLE_CAIXA_RESPONSE)
        assert result.dezenas == sorted(result.dezenas)

    def test_not_acumulado(self):
        result = _parse_response(SAMPLE_CAIXA_RESPONSE)
        assert result.acumulado is False

    def test_acumulado_flag(self):
        result = _parse_response(SAMPLE_ACUMULADO_RESPONSE)
        assert result.acumulado is True

    def test_premiacoes_count(self):
        result = _parse_response(SAMPLE_CAIXA_RESPONSE)
        assert len(result.premiacoes) == 3

    def test_sena_prize_tier(self):
        result = _parse_response(SAMPLE_CAIXA_RESPONSE)
        sena = result.premiacoes[0]
        assert sena.tier == 1
        assert sena.winners == 2
        assert sena.prize_amount == 45_000_000.0

    def test_date_iso_format(self):
        result = _parse_response(SAMPLE_CAIXA_RESPONSE)
        assert result.data_apuracao_iso == "2026-04-05"

    def test_next_concurso(self):
        result = _parse_response(SAMPLE_CAIXA_RESPONSE)
        assert result.concurso_proximo == 2851


# ── Summary tests ──────────────────────────────────────────


class TestBuildSummary:
    def test_summary_with_winners(self):
        result = _parse_response(SAMPLE_CAIXA_RESPONSE)
        summary = _build_summary(result)
        assert "2850" in summary
        assert "dezenas" in summary.lower() or "04" in summary

    def test_summary_acumulado(self):
        result = _parse_response(SAMPLE_ACUMULADO_RESPONSE)
        summary = _build_summary(result)
        assert "ACUMULOU" in summary
        assert "120.000.000" in summary or "120,000,000" in summary or "120" in summary

    def test_summary_contains_date(self):
        result = _parse_response(SAMPLE_CAIXA_RESPONSE)
        summary = _build_summary(result)
        assert "05/04/2026" in summary


# ── Vocabulary tests ───────────────────────────────────────


class TestVocab:
    def test_mega_sena_content_type_uri(self):
        ct = LotteryContentTypes.MEGA_SENA
        assert ct == "https://signed-data.org/vocab/lottery-brazil/mega-sena-result"

    def test_caixa_source_uri(self):
        src = CDSSources.CAIXA_LOTERIAS
        assert src == "https://signed-data.org/sources/caixa.gov.br.loterias.v1"

    def test_content_type_matches_cdsvocab(self):
        assert LotteryContentTypes.MEGA_SENA == CDSVocab.LOTTERY_MEGA_SENA


# ── Ingestor tests (mocked) ────────────────────────────────


class TestMegaSenaIngestor:
    @pytest.mark.asyncio
    async def test_fetch_returns_events(self, signer):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_CAIXA_RESPONSE
        mock_response.content = b'{"numero": 2850}'
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            ingestor = MegaSenaIngestor(signer=signer)
            events = await ingestor.fetch()

        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_fetch_event_content_type(self, signer):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_CAIXA_RESPONSE
        mock_response.content = b'{"numero": 2850}'
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            ingestor = MegaSenaIngestor(signer=signer)
            events = await ingestor.fetch()

        assert events[0].content_type == LotteryContentTypes.MEGA_SENA

    @pytest.mark.asyncio
    async def test_fetch_event_payload_concurso(self, signer):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_CAIXA_RESPONSE
        mock_response.content = b'{"numero": 2850}'
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            ingestor = MegaSenaIngestor(signer=signer)
            events = await ingestor.fetch()

        assert events[0].payload["concurso"] == 2850

    @pytest.mark.asyncio
    async def test_ingest_event_signed(self, signer, verifier):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_CAIXA_RESPONSE
        mock_response.content = b'{"numero": 2850}'
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            ingestor = MegaSenaIngestor(signer=signer)
            events = await ingestor.ingest()

        event = events[0]
        assert event.integrity is not None
        assert verifier.verify(event)

    @pytest.mark.asyncio
    async def test_fetch_multiple_concursos(self, signer):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_CAIXA_RESPONSE
        mock_response.content = b'{"numero": 2850}'
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            ingestor = MegaSenaIngestor(signer=signer, concursos=[2848, 2849, 2850])
            events = await ingestor.fetch()

        assert len(events) == 3


# ── Model serialization tests ──────────────────────────────


class TestMegaSenaResultModel:
    def test_dezenas_formatted(self):
        result = _parse_response(SAMPLE_CAIXA_RESPONSE)
        fmt = result.dezenas_formatted
        assert "·" in fmt
        assert "04" in fmt

    def test_model_dump_mode_json(self):
        result = _parse_response(SAMPLE_CAIXA_RESPONSE)
        data = result.model_dump(mode="json")
        assert isinstance(data["concurso"], int)
        assert isinstance(data["dezenas"], list)
        assert isinstance(data["premiacoes"], list)

    def test_prize_tier_total(self):
        result = _parse_response(SAMPLE_CAIXA_RESPONSE)
        sena = result.premiacoes[0]
        assert sena.total_prize == sena.winners * sena.prize_amount


# ── Server tool count check ────────────────────────────────


class TestLotteryServerTools:
    def test_five_tools_in_server_file(self):
        from pathlib import Path

        server_path = (
            Path(__file__).parent.parent.parent.parent / "mcp/lottery/server.py"
        )
        source = server_path.read_text()
        expected_tools = [
            "get_mega_sena_latest",
            "get_mega_sena_by_concurso",
            "get_mega_sena_recent",
            "check_mega_sena_ticket",
            "get_mega_sena_statistics",
        ]
        for tool in expected_tools:
            assert f"async def {tool}" in source, f"Missing tool: {tool}"
