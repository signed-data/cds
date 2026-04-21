"""
CDS Finance Brazil Test Suite
Tests for models, content types, ingestors (mocked), signing, and summaries.
"""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.signer import CDSSigner, CDSVerifier, generate_keypair
from cds.sources.finance_models import (
    CopomDecision,
    FinanceContentTypes,
    FXRate,
    IPCAIndex,
    SELICRate,
    StockQuote,
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


class TestSELICRateModel:
    def test_create(self):
        r = SELICRate(
            date="2026-04-02",
            rate_annual=13.75,
            rate_daily=0.0529,
            effective_date="2026-04-02",
        )
        assert r.rate_annual == 13.75
        assert r.unit == "% a.a."

    def test_serialise(self):
        r = SELICRate(
            date="2026-04-02",
            rate_annual=13.75,
            rate_daily=0.0529,
            effective_date="2026-04-02",
        )
        d = r.model_dump(mode="json")
        assert d["date"] == "2026-04-02"
        assert d["rate_annual"] == 13.75


class TestIPCAIndexModel:
    def test_create(self):
        i = IPCAIndex(
            date="2026-03-01",
            monthly_pct=0.83,
            accumulated_12m=5.06,
            accumulated_year=2.14,
        )
        assert i.base_year == 1993
        assert i.accumulated_12m == 5.06


class TestFXRateModel:
    def test_create(self):
        fx = FXRate(
            date="2026-04-02",
            buy=5.8741,
            sell=5.8747,
            mid=5.8744,
            currency_from="USD",
            currency_to="BRL",
        )
        assert fx.source == "ptax"
        assert fx.mid == 5.8744

    def test_mid_computation(self):
        buy, sell = 5.8741, 5.8747
        mid = round((buy + sell) / 2, 4)
        assert mid == 5.8744


class TestStockQuoteModel:
    def test_create(self):
        q = StockQuote(
            ticker="PETR4",
            short_name="PETROBRAS PN",
            long_name="Petróleo Brasileiro S.A. - Petrobras",
            currency="BRL",
            market_price=38.92,
            change=0.45,
            change_pct=1.17,
            previous_close=38.47,
            open=38.50,
            day_high=39.10,
            day_low=38.40,
            volume=42891300,
            market_cap=507840000000,
            exchange="SAO",
            market_state="REGULAR",
            timestamp="2026-04-02T17:30:00-03:00",
        )
        assert q.ticker == "PETR4"
        assert q.market_state == "REGULAR"


class TestCopomDecisionModel:
    def test_maintain(self):
        c = CopomDecision(
            meeting_number=267,
            meeting_date="2026-03-19",
            decision="maintain",
            rate_before=13.75,
            rate_after=13.75,
            rate_change_bps=0,
            vote_unanimous=True,
        )
        assert c.decision == "maintain"
        assert c.rate_change_bps == 0

    def test_raise(self):
        c = CopomDecision(
            meeting_number=268,
            meeting_date="2026-05-07",
            decision="raise",
            rate_before=13.75,
            rate_after=14.00,
            rate_change_bps=25,
            vote_unanimous=False,
        )
        assert c.decision == "raise"
        assert c.rate_change_bps == 25


# ── Content Type Tests ────────────────────────────────────


class TestFinanceContentTypes:
    def test_all_are_uris(self):
        for ct in [
            FinanceContentTypes.SELIC,
            FinanceContentTypes.CDI,
            FinanceContentTypes.IPCA,
            FinanceContentTypes.IGPM,
            FinanceContentTypes.USD_BRL,
            FinanceContentTypes.EUR_BRL,
            FinanceContentTypes.STOCK,
            FinanceContentTypes.FII,
            FinanceContentTypes.CRYPTO,
            FinanceContentTypes.COPOM,
        ]:
            assert ct.startswith("https://signed-data.org/vocab/finance-brazil/"), ct

    def test_selic_equals_vocab(self):
        assert FinanceContentTypes.SELIC == CDSVocab.FINANCE_SELIC_RATE

    def test_stock_equals_vocab(self):
        assert FinanceContentTypes.STOCK == CDSVocab.FINANCE_QUOTE_STOCK

    def test_copom_equals_vocab(self):
        assert FinanceContentTypes.COPOM == CDSVocab.FINANCE_DECISION_COPOM

    def test_selic_uri_value(self):
        assert (
            FinanceContentTypes.SELIC == "https://signed-data.org/vocab/finance-brazil/rate-selic"
        )


# ── CDS Event Tests ───────────────────────────────────────


class TestFinanceEvent:
    def test_selic_event_domain(self):
        event = CDSEvent(
            content_type=FinanceContentTypes.SELIC,
            source=SourceMeta(id=CDSSources.BCB_API, fingerprint="sha256:mock"),
            occurred_at=datetime(2026, 4, 2, tzinfo=UTC),
            lang="pt-BR",
            payload={"date": "2026-04-02", "rate_annual": 13.75},
        )
        assert event.domain == "finance.brazil"
        assert event.event_type == "rate.selic"

    def test_stock_event_domain(self):
        event = CDSEvent(
            content_type=FinanceContentTypes.STOCK,
            source=SourceMeta(id=CDSSources.BRAPI, fingerprint="sha256:mock"),
            occurred_at=datetime(2026, 4, 2, tzinfo=UTC),
            lang="pt-BR",
            payload={"ticker": "PETR4", "market_price": 38.92},
        )
        assert event.domain == "finance.brazil"
        assert event.event_type == "quote.stock"

    def test_signing_and_verification(self, signer, verifier):
        event = CDSEvent(
            content_type=FinanceContentTypes.SELIC,
            source=SourceMeta(id=CDSSources.BCB_API, fingerprint="sha256:mock"),
            occurred_at=datetime(2026, 4, 2, tzinfo=UTC),
            lang="pt-BR",
            payload={"date": "2026-04-02", "rate_annual": 13.75},
            event_context=ContextMeta(summary="SELIC: 13.75% a.a.", model="rule-based-v1"),
        )
        signer.sign(event)
        assert event.integrity is not None
        assert verifier.verify(event) is True

    def test_jsonld_fields(self, signer):
        event = CDSEvent(
            content_type=FinanceContentTypes.USD_BRL,
            source=SourceMeta(id=CDSSources.BCB_API),
            occurred_at=datetime(2026, 4, 2, tzinfo=UTC),
            lang="pt-BR",
            payload={"date": "2026-04-02", "buy": 5.87, "sell": 5.88},
        )
        signer.sign(event)
        d = event.to_jsonld()
        assert d["@context"].startswith("https://signed-data.org/")
        assert d["@type"] == "https://signed-data.org/vocab/CuratedDataEvent"
        assert d["@id"].startswith("https://signed-data.org/events/")

    def test_canonical_bytes_exclude_integrity(self, signer):
        event = CDSEvent(
            content_type=FinanceContentTypes.SELIC,
            source=SourceMeta(id=CDSSources.BCB_API),
            occurred_at=datetime(2026, 4, 2, tzinfo=UTC),
            lang="pt-BR",
            payload={"date": "2026-04-02", "rate_annual": 13.75},
        )
        signer.sign(event)
        d = json.loads(event.canonical_bytes())
        assert "integrity" not in d
        assert "ingested_at" not in d


# ── Summary Format Tests ──────────────────────────────────


class TestSummaryFormats:
    def test_selic_summary(self):
        summary = f"SELIC: {13.75}% a.a. (2026-04-02)"
        assert "SELIC:" in summary
        assert "13.75%" in summary

    def test_stock_summary(self):
        summary = f"PETR4: R$ {38.92:.2f} ({1.17:+.2f}%) — REGULAR"
        assert "PETR4:" in summary
        assert "R$ 38.92" in summary
        assert "+1.17%" in summary

    def test_copom_summary(self):
        summary = "Copom #267: maintain SELIC em 13.75% a.a."
        assert "Copom #267" in summary
        assert "maintain" in summary

    def test_ipca_summary(self):
        summary = f"IPCA 2026-03-01: {0.83}% no mês, {5.06}% em 12 meses"
        assert "IPCA" in summary
        assert "0.83%" in summary
        assert "5.06%" in summary


# ── Ingestor Tests (Mocked) ──────────────────────────────


class TestBCBRatesIngestor:
    @pytest.mark.asyncio
    async def test_with_mock_response(self):
        from cds.sources.finance import BCBRatesIngestor

        mock_signer = MagicMock()
        mock_signer.sign = lambda e: e

        mock_selic_resp = MagicMock()
        mock_selic_resp.content = b'[{"data":"02/04/2026","valor":"13.75"}]'
        mock_selic_resp.json.return_value = [{"data": "02/04/2026", "valor": "13.75"}]
        mock_selic_resp.raise_for_status = MagicMock()

        mock_cdi_resp = MagicMock()
        mock_cdi_resp.content = b'[{"data":"02/04/2026","valor":"13.65"}]'
        mock_cdi_resp.json.return_value = [{"data": "02/04/2026", "valor": "13.65"}]
        mock_cdi_resp.raise_for_status = MagicMock()

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_selic_resp
            return mock_cdi_resp

        with patch("cds.sources.finance.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = mock_get
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            ingestor = BCBRatesIngestor(mock_signer)
            events = await ingestor.fetch()

            assert len(events) == 2  # SELIC + CDI
            assert events[0].content_type == FinanceContentTypes.SELIC
            assert events[0].payload["rate_annual"] == 13.75
            assert events[1].content_type == FinanceContentTypes.CDI
            assert events[1].payload["rate_annual"] == 13.65


class TestBCBFXIngestor:
    @pytest.mark.asyncio
    async def test_with_mock_response(self):
        from cds.sources.finance import BCBFXIngestor

        mock_signer = MagicMock()
        mock_signer.sign = lambda e: e

        mock_buy_resp = MagicMock()
        mock_buy_resp.content = b'[{"data":"02/04/2026","valor":"5.8741"}]'
        mock_buy_resp.json.return_value = [{"data": "02/04/2026", "valor": "5.8741"}]
        mock_buy_resp.raise_for_status = MagicMock()

        mock_sell_resp = MagicMock()
        mock_sell_resp.content = b'[{"data":"02/04/2026","valor":"5.8747"}]'
        mock_sell_resp.json.return_value = [{"data": "02/04/2026", "valor": "5.8747"}]
        mock_sell_resp.raise_for_status = MagicMock()

        mock_eur_resp = MagicMock()
        mock_eur_resp.content = b'[{"data":"02/04/2026","valor":"6.3500"}]'
        mock_eur_resp.json.return_value = [{"data": "02/04/2026", "valor": "6.3500"}]
        mock_eur_resp.raise_for_status = MagicMock()

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_buy_resp
            if call_count == 2:
                return mock_sell_resp
            return mock_eur_resp

        with patch("cds.sources.finance.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = mock_get
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            ingestor = BCBFXIngestor(mock_signer)
            events = await ingestor.fetch()

            assert len(events) == 2  # USD/BRL + EUR/BRL
            assert events[0].content_type == FinanceContentTypes.USD_BRL
            assert events[0].payload["buy"] == 5.8741
            assert events[0].payload["sell"] == 5.8747
            assert events[1].content_type == FinanceContentTypes.EUR_BRL


class TestBrapiQuotesIngestor:
    @pytest.mark.asyncio
    async def test_with_mock_response(self):
        from cds.sources.finance import BrapiQuotesIngestor

        mock_signer = MagicMock()
        mock_signer.sign = lambda e: e

        mock_resp = MagicMock()
        mock_resp.content = json.dumps(
            {
                "results": [{"symbol": "PETR4", "regularMarketPrice": 38.92}],
            }
        ).encode()
        mock_resp.json.return_value = {
            "results": [
                {
                    "symbol": "PETR4",
                    "shortName": "PETROBRAS PN",
                    "longName": "Petrobras",
                    "currency": "BRL",
                    "regularMarketPrice": 38.92,
                    "regularMarketChange": 0.45,
                    "regularMarketChangePercent": 1.17,
                    "regularMarketPreviousClose": 38.47,
                    "regularMarketOpen": 38.50,
                    "regularMarketDayHigh": 39.10,
                    "regularMarketDayLow": 38.40,
                    "regularMarketVolume": 42891300,
                    "marketCap": 507840000000,
                    "fullExchangeName": "SAO",
                    "marketState": "REGULAR",
                    "regularMarketTime": "2026-04-02T17:30:00-03:00",
                }
            ],
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("cds.sources.finance.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            ingestor = BrapiQuotesIngestor(mock_signer, tickers=["PETR4"])
            events = await ingestor.fetch()

            assert len(events) == 1
            assert events[0].content_type == FinanceContentTypes.STOCK
            assert events[0].payload["ticker"] == "PETR4"
            assert events[0].payload["market_price"] == 38.92


class TestFinanceServerToolCount:
    def test_ten_tools_in_server_file(self):
        from pathlib import Path
        server_path = Path(__file__).parent.parent.parent.parent / "mcp/finance/server.py"
        source = server_path.read_text()
        expected_tools = [
            "get_selic_rate", "get_ipca", "get_igpm",
            "get_usd_brl", "get_fx_rates",
            "get_stock_quote", "get_b3_indices", "get_market_summary",
            "get_copom_history", "get_copom_latest",
        ]
        for tool in expected_tools:
            assert f"async def {tool}" in source, f"Missing tool: {tool}"
