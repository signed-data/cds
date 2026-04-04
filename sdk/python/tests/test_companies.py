"""
CDS Companies Brazil Test Suite
Tests for CNPJ validation, models, fetcher (mocked), event signing, summaries.
"""
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.signer import CDSSigner, CDSVerifier, generate_keypair
from cds.sources.companies_models import (
    CNAECode,
    CompaniesContentTypes,
    CompanyAddress,
    CompanyPartner,
    CompanyPartners,
    CompanyProfile,
)
from cds.sources.companies import (
    CNPJFetcher,
    validate_cnpj,
    _build_profile_summary,
    _format_cnpj,
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


# ── CNPJ Validation Tests ─────────────────────────────────


class TestCNPJValidation:
    def test_valid_cnpj_bare(self):
        # Petrobras CNPJ (real)
        result = validate_cnpj("33000167000101")
        assert result == "33000167000101"

    def test_valid_cnpj_formatted(self):
        result = validate_cnpj("33.000.167/0001-01")
        assert result == "33000167000101"

    def test_invalid_check_digits(self):
        with pytest.raises(ValueError, match="check digit"):
            validate_cnpj("33000167000199")

    def test_too_short(self):
        with pytest.raises(ValueError, match="14 digits"):
            validate_cnpj("1234567890")

    def test_too_long(self):
        with pytest.raises(ValueError, match="14 digits"):
            validate_cnpj("123456789012345")

    def test_non_numeric(self):
        with pytest.raises(ValueError, match="14 digits"):
            validate_cnpj("ABCDEFGHIJKLMN")

    def test_all_same_digits(self):
        with pytest.raises(ValueError, match="same digits"):
            validate_cnpj("11111111111111")

    def test_format_cnpj(self):
        assert _format_cnpj("33000167000101") == "33.000.167/0001-01"

    def test_another_valid_cnpj(self):
        # Banco do Brasil
        result = validate_cnpj("00000000000191")
        assert result == "00000000000191"


# ── Model Tests ───────────────────────────────────────────


class TestCompanyProfileModel:
    def test_active_company(self):
        profile = CompanyProfile(
            cnpj="33000167000101",
            cnpj_formatted="33.000.167/0001-01",
            company_name="PETRÓLEO BRASILEIRO S A PETROBRAS",
            trade_name="PETROBRAS",
            registration_status="ATIVA",
            registration_date="1953-10-03",
            legal_nature_code="2038",
            legal_nature="Sociedade Anônima Aberta",
            size="DEMAIS",
            share_capital=205431960490.52,
            main_cnae=CNAECode(code="0610600", description="Extração de petróleo e gás natural"),
            address=CompanyAddress(
                street="AV REPÚBLICA DO CHILE",
                number="65",
                neighborhood="CENTRO",
                zip_code="20031170",
                city="RIO DE JANEIRO",
                state="RJ",
            ),
            query_timestamp="2026-04-02T14:30:00-03:00",
        )
        assert profile.is_active is True
        assert profile.cnpj == "33000167000101"

    def test_inactive_company(self):
        profile = CompanyProfile(
            cnpj="00000000000000",
            cnpj_formatted="00.000.000/0000-00",
            company_name="ACME LTDA",
            registration_status="BAIXADA",
            registration_date="2010-01-01",
            legal_nature_code="2062",
            legal_nature="Sociedade Empresária Limitada",
            size="ME",
            main_cnae=CNAECode(code="4711302", description="Comércio varejista"),
            address=CompanyAddress(
                street="RUA A", number="1",
                neighborhood="CENTRO", zip_code="01000000",
                city="SÃO PAULO", state="SP",
            ),
            query_timestamp="2026-04-02T14:30:00-03:00",
        )
        assert profile.is_active is False


class TestCompanyPartnersModel:
    def test_create(self):
        partners = CompanyPartners(
            cnpj="33000167000101",
            company_name="PETROBRAS",
            partners=[
                CompanyPartner(
                    name="UNIÃO FEDERAL",
                    qualifier="Sócio Pessoa Jurídica",
                    qualifier_code=49,
                    entry_date="2005-11-19",
                ),
            ],
            query_timestamp="2026-04-02T14:30:00-03:00",
        )
        assert len(partners.partners) == 1
        assert partners.partners[0].name == "UNIÃO FEDERAL"


# ── Content Type Tests ────────────────────────────────────


class TestCompaniesContentTypes:
    def test_all_are_uris(self):
        for ct in [
            CompaniesContentTypes.PROFILE,
            CompaniesContentTypes.PARTNERS,
            CompaniesContentTypes.CNAE,
        ]:
            assert ct.startswith("https://signed-data.org/vocab/companies-brazil/"), ct

    def test_profile_equals_vocab(self):
        assert CompaniesContentTypes.PROFILE == CDSVocab.COMPANIES_PROFILE_CNPJ

    def test_profile_uri_value(self):
        assert CompaniesContentTypes.PROFILE == \
            "https://signed-data.org/vocab/companies-brazil/profile-cnpj"


# ── Event Tests ───────────────────────────────────────────


class TestCompanyEvent:
    def test_domain(self):
        event = CDSEvent(
            content_type=CompaniesContentTypes.PROFILE,
            source=SourceMeta(id=CDSSources.BRASILAPI, fingerprint="sha256:mock"),
            occurred_at=datetime(2026, 4, 2, tzinfo=UTC),
            lang="pt-BR",
            payload={"cnpj": "33000167000101", "company_name": "PETROBRAS"},
        )
        assert event.domain == "companies.brazil"
        assert event.event_type == "profile.cnpj"

    def test_signing_and_verification(self, signer, verifier):
        event = CDSEvent(
            content_type=CompaniesContentTypes.PROFILE,
            source=SourceMeta(id=CDSSources.BRASILAPI, fingerprint="sha256:mock"),
            occurred_at=datetime(2026, 4, 2, tzinfo=UTC),
            lang="pt-BR",
            payload={"cnpj": "33000167000101"},
            event_context=ContextMeta(summary="PETROBRAS", model="rule-based-v1"),
        )
        signer.sign(event)
        assert verifier.verify(event) is True

    def test_jsonld_fields(self):
        event = CDSEvent(
            content_type=CompaniesContentTypes.PARTNERS,
            source=SourceMeta(id=CDSSources.BRASILAPI),
            occurred_at=datetime(2026, 4, 2, tzinfo=UTC),
            lang="pt-BR",
            payload={"cnpj": "33000167000101", "partners": []},
        )
        d = event.to_jsonld()
        assert d["content_type"].startswith("https://signed-data.org/vocab/")
        assert d["source"]["@id"].startswith("https://signed-data.org/sources/")


# ── Summary Tests ─────────────────────────────────────────


class TestSummary:
    def test_active_company(self):
        profile = CompanyProfile(
            cnpj="33000167000101",
            cnpj_formatted="33.000.167/0001-01",
            company_name="PETRÓLEO BRASILEIRO S A PETROBRAS",
            trade_name="PETROBRAS",
            registration_status="ATIVA",
            registration_date="1953-10-03",
            legal_nature_code="2038",
            legal_nature="Sociedade Anônima Aberta",
            size="DEMAIS",
            share_capital=205431960490.52,
            main_cnae=CNAECode(code="0610600", description="Extração de petróleo"),
            address=CompanyAddress(
                street="AV", number="65", neighborhood="CENTRO",
                zip_code="20031170", city="RIO DE JANEIRO", state="RJ",
            ),
            query_timestamp="2026-04-02T14:30:00-03:00",
        )
        summary = _build_profile_summary(profile)
        assert "PETROBRAS" in summary
        assert "ATIVA" in summary
        assert "1953-10-03" in summary

    def test_inactive_company(self):
        profile = CompanyProfile(
            cnpj="00000000000000",
            cnpj_formatted="00.000.000/0000-00",
            company_name="ACME LTDA",
            registration_status="BAIXADA",
            registration_date="2010-01-01",
            legal_nature_code="2062",
            legal_nature="Limitada",
            size="ME",
            main_cnae=CNAECode(code="4711302", description="Comércio varejista"),
            address=CompanyAddress(
                street="R", number="1", neighborhood="C",
                zip_code="01000000", city="SP", state="SP",
            ),
            query_timestamp="2026-04-02T14:30:00-03:00",
        )
        summary = _build_profile_summary(profile)
        assert "ACME LTDA" in summary
        assert "BAIXADA" in summary


# ── Fetcher Tests (Mocked) ───────────────────────────────


MOCK_BRASILAPI_RESPONSE = {
    "cnpj": 33000167000101,
    "razao_social": "PETRÓLEO BRASILEIRO S A PETROBRAS",
    "nome_fantasia": "PETROBRAS",
    "descricao_situacao_cadastral": "ATIVA",
    "data_inicio_atividade": "1953-10-03",
    "codigo_natureza_juridica": "2038",
    "natureza_juridica": "Sociedade Anônima Aberta",
    "porte": "DEMAIS",
    "capital_social": 205431960490.52,
    "cnae_fiscal": 610600,
    "cnae_fiscal_descricao": "Extração de petróleo e gás natural",
    "cnaes_secundarios": [
        {"codigo": 1921700, "descricao": "Fabricação de produtos do refino de petróleo"},
    ],
    "logradouro": "AV REPÚBLICA DO CHILE",
    "numero": "65",
    "complemento": "ANDAR 1 A 20",
    "bairro": "CENTRO",
    "cep": "20031170",
    "municipio": "RIO DE JANEIRO",
    "uf": "RJ",
    "ddd_telefone_1": "2125342000",
    "email": None,
    "qsa": [
        {
            "nome_socio": "UNIÃO FEDERAL - PODER EXECUTIVO",
            "qualificacao_socio": "Sócio Pessoa Jurídica",
            "codigo_qualificacao_socio": 49,
            "data_entrada_sociedade": "2005-11-19",
            "pais": None,
            "nome_representante_legal": None,
        },
    ],
}


class TestCNPJFetcher:
    @pytest.mark.asyncio
    async def test_fetch_profile_with_mock(self):
        mock_resp = MagicMock()
        mock_resp.content = json.dumps(MOCK_BRASILAPI_RESPONSE).encode()
        mock_resp.json.return_value = MOCK_BRASILAPI_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        with patch("cds.sources.companies.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            fetcher = CNPJFetcher()
            event = await fetcher.fetch_profile("33.000.167/0001-01")

            assert event.content_type == CompaniesContentTypes.PROFILE
            assert event.payload["company_name"] == "PETRÓLEO BRASILEIRO S A PETROBRAS"
            assert event.payload["cnpj"] == "33000167000101"
            assert event.domain == "companies.brazil"

    @pytest.mark.asyncio
    async def test_fetch_partners_with_mock(self):
        mock_resp = MagicMock()
        mock_resp.content = json.dumps(MOCK_BRASILAPI_RESPONSE).encode()
        mock_resp.json.return_value = MOCK_BRASILAPI_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        with patch("cds.sources.companies.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            fetcher = CNPJFetcher()
            event = await fetcher.fetch_partners("33.000.167/0001-01")

            assert event.content_type == CompaniesContentTypes.PARTNERS
            assert len(event.payload["partners"]) == 1
            assert event.payload["partners"][0]["name"] == "UNIÃO FEDERAL - PODER EXECUTIVO"

    @pytest.mark.asyncio
    async def test_invalid_cnpj_raises(self):
        fetcher = CNPJFetcher()
        with pytest.raises(ValueError, match="check digit"):
            await fetcher.fetch_profile("11222333000199")
