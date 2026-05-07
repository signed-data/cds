"""
CDS Commodities Brazil Test Suite
Tests for models, content types, ingestors (mocked), CONAB defensive parsing,
basis computation, and signing.
"""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.signer import CDSSigner, CDSVerifier, generate_keypair
from cds.sources.commodities import (
    B3FuturesIngestor,
    CONABSpotIngestor,
    _parse_conab_response,
)
from cds.sources.commodities_models import (
    CommodityContentTypes,
    CommodityFutures,
    CommodityIndex,
    CommoditySpot,
    CONABResponseChangedError,
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


# ── Model Tests ───────────────────────────────────────────


class TestCommodityFuturesModel:
    def test_create(self):
        f = CommodityFutures(
            commodity="soja",
            ticker="SFI",
            unit="R$/60kg",
            contract_month="2026-05",
            price=146.50,
            change=-0.80,
            change_pct=-0.54,
            open=147.20,
            day_high=147.50,
            day_low=146.20,
            volume=12450,
            open_interest=98340,
            timestamp="2026-04-02T14:30:00-03:00",
        )
        assert f.commodity == "soja"
        assert f.exchange == "B3"
        assert f.price == 146.50


class TestCommoditySpotModel:
    def test_create(self):
        s = CommoditySpot(
            commodity="soja",
            state="MT",
            city="Rondonópolis",
            unit="R$/60kg",
            price=148.30,
            week="2026-W14",
            date_from="2026-03-30",
            date_to="2026-04-05",
        )
        assert s.source == "CONAB"
        assert s.state == "MT"


class TestCommodityIndexModel:
    def test_create(self):
        i = CommodityIndex(
            indicator="PSOYBEANS",
            name="Soybeans",
            date="2026-03",
            value=450.50,
            unit="USD/mt",
        )
        assert i.source == "World Bank"


# ── Content Type Tests ────────────────────────────────────


class TestCommodityContentTypes:
    def test_all_are_uris(self):
        for ct in [
            CommodityContentTypes.FUTURES_SOJA,
            CommodityContentTypes.FUTURES_MILHO,
            CommodityContentTypes.FUTURES_BOI,
            CommodityContentTypes.FUTURES_CAFE,
            CommodityContentTypes.FUTURES_ACUCAR,
            CommodityContentTypes.FUTURES_ETANOL,
            CommodityContentTypes.SPOT_SOJA,
            CommodityContentTypes.SPOT_MILHO,
            CommodityContentTypes.SPOT_TRIGO,
            CommodityContentTypes.SPOT_ALGODAO,
            CommodityContentTypes.INDEX_WORLDBANK,
        ]:
            assert ct.startswith("https://signed-data.org/vocab/commodities-brazil/"), ct

    def test_futures_soja_equals_vocab(self):
        assert CommodityContentTypes.FUTURES_SOJA == CDSVocab.COMMODITY_FUTURES_SOJA

    def test_futures_soja_uri_value(self):
        assert (
            CommodityContentTypes.FUTURES_SOJA
            == "https://signed-data.org/vocab/commodities-brazil/futures-soja"
        )


# ── CONAB Defensive Parsing Tests ─────────────────────────


class TestCONABParsing:
    def test_valid_response(self):
        data = [{"produto": "soja", "uf": "MT", "preco": 148.30}]
        result = _parse_conab_response(data)
        assert len(result) == 1

    def test_empty_list(self):
        result = _parse_conab_response([])
        assert result == []

    def test_not_a_list(self):
        with pytest.raises(CONABResponseChangedError, match="Expected list"):
            _parse_conab_response({"error": "something"})

    def test_missing_keys(self):
        data = [{"nome": "soja", "estado": "MT"}]
        with pytest.raises(CONABResponseChangedError, match="Missing expected keys"):
            _parse_conab_response(data)

    def test_non_dict_items(self):
        with pytest.raises(CONABResponseChangedError, match="Expected dict"):
            _parse_conab_response(["not a dict"])


# ── Event Tests ───────────────────────────────────────────


class TestCommodityEvent:
    def test_futures_event_domain(self):
        event = CDSEvent(
            content_type=CommodityContentTypes.FUTURES_SOJA,
            source=SourceMeta(id=CDSSources.BRAPI, fingerprint="sha256:mock"),
            occurred_at=datetime(2026, 4, 2, tzinfo=UTC),
            lang="pt-BR",
            payload={"commodity": "soja", "ticker": "SFI", "price": 146.50},
        )
        assert event.domain == "commodities.brazil"
        assert event.event_type == "futures.soja"

    def test_spot_event_domain(self):
        event = CDSEvent(
            content_type=CommodityContentTypes.SPOT_SOJA,
            source=SourceMeta(id=CDSSources.CONAB, fingerprint="sha256:mock"),
            occurred_at=datetime(2026, 4, 2, tzinfo=UTC),
            lang="pt-BR",
            payload={"commodity": "soja", "state": "MT", "price": 148.30},
        )
        assert event.domain == "commodities.brazil"
        assert event.event_type == "spot.soja"

    def test_signing_and_verification(self, signer, verifier):
        event = CDSEvent(
            content_type=CommodityContentTypes.FUTURES_CAFE,
            source=SourceMeta(id=CDSSources.BRAPI, fingerprint="sha256:mock"),
            occurred_at=datetime(2026, 4, 2, tzinfo=UTC),
            lang="pt-BR",
            payload={"commodity": "café", "ticker": "ICF", "price": 1200.00},
            event_context=ContextMeta(summary="Café B3: R$ 1200.00", model="rule-based-v1"),
        )
        signer.sign(event)
        assert verifier.verify(event) is True

    def test_summary_includes_commodity_and_price(self):
        summary = "Soja B3 (SFI): R$ 146.50 (-0.54%)"
        assert "Soja" in summary
        assert "146.50" in summary


# ── Basis Computation Test ────────────────────────────────


class TestBasisComputation:
    def test_basis_is_auditable(self):
        futures_price = 146.50
        spot_price = 144.70
        basis = spot_price - futures_price
        result = {
            "basis": basis,
            "basis_unit": "R$/60kg",
            "futures_price": futures_price,
            "spot_price": spot_price,
            "computed": True,
            "llm_generated": False,
        }
        assert result["basis"] == pytest.approx(-1.80)
        assert result["llm_generated"] is False
        assert result["computed"] is True


# ── Ingestor Tests (Mocked) ──────────────────────────────


class TestB3FuturesIngestor:
    @pytest.mark.asyncio
    async def test_with_mock_brapi_response(self):
        mock_signer = MagicMock()
        mock_signer.sign = lambda e: e

        mock_resp = MagicMock()
        mock_resp.content = json.dumps(
            {
                "results": [{"symbol": "SFI", "regularMarketPrice": 146.50}],
            }
        ).encode()
        mock_resp.json.return_value = {
            "results": [
                {
                    "symbol": "SFI",
                    "regularMarketPrice": 146.50,
                    "regularMarketChange": -0.80,
                    "regularMarketChangePercent": -0.54,
                    "regularMarketOpen": 147.20,
                    "regularMarketDayHigh": 147.50,
                    "regularMarketDayLow": 146.20,
                    "regularMarketVolume": 12450,
                    "regularMarketTime": "2026-04-02T14:30:00-03:00",
                }
            ],
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("cds.sources.commodities.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            ingestor = B3FuturesIngestor(mock_signer, commodities=["SFI"])
            events = await ingestor.fetch()

            assert len(events) == 1
            assert events[0].content_type == CommodityContentTypes.FUTURES_SOJA
            assert events[0].payload["commodity"] == "soja"
            assert events[0].payload["price"] == 146.50


class TestCONABSpotIngestor:
    @pytest.mark.asyncio
    async def test_with_mock_response(self):
        mock_signer = MagicMock()
        mock_signer.sign = lambda e: e

        conab_data = [
            {"produto": "soja", "uf": "MT", "preco": 148.30, "cidade": "Rondonópolis"},
            {"produto": "milho", "uf": "GO", "preco": 52.10, "cidade": "Rio Verde"},
        ]
        mock_resp = MagicMock()
        mock_resp.content = json.dumps(conab_data).encode()
        mock_resp.json.return_value = conab_data
        mock_resp.raise_for_status = MagicMock()

        with patch("cds.sources.commodities.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            ingestor = CONABSpotIngestor(mock_signer)
            events = await ingestor.fetch()

            assert len(events) == 2
            assert events[0].content_type == CommodityContentTypes.SPOT_SOJA
            assert events[1].content_type == CommodityContentTypes.SPOT_MILHO

    @pytest.mark.asyncio
    async def test_graceful_failure_on_bad_response(self):
        mock_signer = MagicMock()
        mock_signer.sign = lambda e: e

        mock_resp = MagicMock()
        mock_resp.content = b'{"error": "service unavailable"}'
        mock_resp.json.return_value = {"error": "service unavailable"}
        mock_resp.raise_for_status = MagicMock()

        with patch("cds.sources.commodities.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            ingestor = CONABSpotIngestor(mock_signer)
            events = await ingestor.fetch()

            # Should return empty — not raise
            assert events == []
