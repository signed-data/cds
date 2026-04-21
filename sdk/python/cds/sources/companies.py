"""
SignedData CDS — Companies Brazil Fetcher
Source: BrasilAPI — https://brasilapi.com.br/api/cnpj/v1/{cnpj}

Query-driven: no scheduled ingestor. Called per CNPJ lookup from the MCP server.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

import httpx

from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.sources.companies_models import (
    CNAECode,
    CompaniesContentTypes,
    CompanyAddress,
    CompanyPartner,
    CompanyPartners,
    CompanyProfile,
)
from cds.vocab import CDSSources

BRASILAPI_CNPJ_BASE = "https://brasilapi.com.br/api/cnpj/v1"
BRASILAPI_CNAE_BASE = "https://brasilapi.com.br/api/cnae/v1"


def _fingerprint(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _format_cnpj(bare: str) -> str:
    """Format bare CNPJ digits: '11222333000144' → '11.222.333/0001-44'"""
    return f"{bare[:2]}.{bare[2:5]}.{bare[5:8]}/{bare[8:12]}-{bare[12:14]}"


def _brl_capital(value: float) -> str:
    """Format BRL: 205431960490.52 → 'R$ 205.431.960.490,52'"""
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def validate_cnpj(cnpj: str) -> str:
    """
    Validate CNPJ check digits and return normalised bare digits.
    Supports both '11.222.333/0001-44' and '11222333000144'.
    Raises ValueError on invalid CNPJ.
    """
    bare = re.sub(r"[.\-/]", "", cnpj)
    if len(bare) != 14 or not bare.isdigit():
        raise ValueError(f"CNPJ must have 14 digits, got: {cnpj!r}")

    # All same digits is invalid
    if len(set(bare)) == 1:
        raise ValueError(f"Invalid CNPJ (all same digits): {cnpj!r}")

    # First check digit
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(bare[i]) * weights1[i] for i in range(12))
    remainder = total % 11
    d1 = 0 if remainder < 2 else 11 - remainder
    if int(bare[12]) != d1:
        raise ValueError(f"Invalid CNPJ check digit 1: {cnpj!r}")

    # Second check digit
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(bare[i]) * weights2[i] for i in range(13))
    remainder = total % 11
    d2 = 0 if remainder < 2 else 11 - remainder
    if int(bare[13]) != d2:
        raise ValueError(f"Invalid CNPJ check digit 2: {cnpj!r}")

    return bare


def _parse_profile(raw: dict[str, Any], query_ts: str) -> CompanyProfile:
    """Parse BrasilAPI CNPJ response into CompanyProfile."""
    cnpj_bare = str(raw.get("cnpj", "")).zfill(14)
    main_cnae_code = str(raw.get("cnae_fiscal", "")).zfill(7)
    main_cnae_desc = raw.get("cnae_fiscal_descricao", "")

    secondary = []
    for s in raw.get("cnaes_secundarios", []):
        code = str(s.get("codigo", "")).zfill(7)
        desc = s.get("descricao", "")
        if code != "0000000":
            secondary.append(CNAECode(code=code, description=desc))

    address = CompanyAddress(
        street=raw.get("logradouro", ""),
        number=raw.get("numero", ""),
        complement=raw.get("complemento") or None,
        neighborhood=raw.get("bairro", ""),
        zip_code=str(raw.get("cep", "")),
        city=raw.get("municipio", ""),
        state=raw.get("uf", ""),
    )

    return CompanyProfile(
        cnpj=cnpj_bare,
        cnpj_formatted=_format_cnpj(cnpj_bare),
        company_name=raw.get("razao_social", ""),
        trade_name=raw.get("nome_fantasia") or None,
        registration_status=raw.get("descricao_situacao_cadastral", "ATIVA"),
        registration_date=raw.get("data_inicio_atividade", ""),
        registration_status_date=raw.get("data_situacao_cadastral"),
        legal_nature_code=str(raw.get("codigo_natureza_juridica", "")),
        legal_nature=raw.get("natureza_juridica", ""),
        size=raw.get("porte", "DEMAIS"),
        share_capital=raw.get("capital_social"),
        main_cnae=CNAECode(code=main_cnae_code, description=main_cnae_desc),
        secondary_cnaes=secondary,
        address=address,
        phone=raw.get("ddd_telefone_1") or None,
        email=raw.get("email") or None,
        query_timestamp=query_ts,
    )


def _parse_partners(raw: dict[str, Any], query_ts: str) -> CompanyPartners:
    """Parse BrasilAPI CNPJ response QSA into CompanyPartners."""
    cnpj_bare = str(raw.get("cnpj", "")).zfill(14)
    partners = []
    for qsa in raw.get("qsa", []):
        partners.append(
            CompanyPartner(
                name=qsa.get("nome_socio", ""),
                qualifier=qsa.get("qualificacao_socio", ""),
                qualifier_code=int(qsa.get("codigo_qualificacao_socio", 0)),
                entry_date=qsa.get("data_entrada_sociedade"),
                country=qsa.get("pais"),
                legal_representative=qsa.get("nome_representante_legal") or None,
            )
        )
    return CompanyPartners(
        cnpj=cnpj_bare,
        company_name=raw.get("razao_social", ""),
        partners=partners,
        query_timestamp=query_ts,
    )


def _build_profile_summary(profile: CompanyProfile) -> str:
    """Build a human-readable summary for a company profile."""
    name = profile.trade_name or profile.company_name
    status = profile.registration_status
    parts = [f"{name} ({profile.cnpj_formatted}): {status}"]

    if profile.registration_date:
        parts[0] += f" desde {profile.registration_date}"

    parts.append(f"CNAE: {profile.main_cnae.description}")

    if profile.share_capital:
        parts.append(f"Capital social: {_brl_capital(profile.share_capital)}")

    return ". ".join(parts) + "."


class CNPJFetcher:
    """
    Fetches and signs CNPJ data on demand.
    Not a scheduled ingestor — called per query from the MCP server.
    """

    def __init__(self, signer: Any = None) -> None:
        self.signer = signer

    async def fetch_profile(self, cnpj: str) -> CDSEvent:
        """Fetch full company profile. Validates CNPJ format first."""
        bare = validate_cnpj(cnpj)
        query_ts = datetime.now(UTC).isoformat()

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{BRASILAPI_CNPJ_BASE}/{bare}")
            resp.raise_for_status()
            fp = _fingerprint(resp.content)
            raw = resp.json()

        profile = _parse_profile(raw, query_ts)
        event = CDSEvent(
            content_type=CompaniesContentTypes.PROFILE,
            source=SourceMeta(id=CDSSources.BRASILAPI, fingerprint=fp),
            occurred_at=datetime.now(UTC),
            lang="pt-BR",
            payload=profile.model_dump(mode="json"),
            event_context=ContextMeta(
                summary=_build_profile_summary(profile),
                model="rule-based-v1",
            ),
        )
        if self.signer:
            self.signer.sign(event)
        return event

    async def fetch_partners(self, cnpj: str) -> CDSEvent:
        """Fetch partner/shareholder data (QSA)."""
        bare = validate_cnpj(cnpj)
        query_ts = datetime.now(UTC).isoformat()

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{BRASILAPI_CNPJ_BASE}/{bare}")
            resp.raise_for_status()
            fp = _fingerprint(resp.content)
            raw = resp.json()

        partners = _parse_partners(raw, query_ts)
        n = len(partners.partners)
        event = CDSEvent(
            content_type=CompaniesContentTypes.PARTNERS,
            source=SourceMeta(id=CDSSources.BRASILAPI, fingerprint=fp),
            occurred_at=datetime.now(UTC),
            lang="pt-BR",
            payload=partners.model_dump(mode="json"),
            event_context=ContextMeta(
                summary=f"{partners.company_name}: {n} sócio{'s' if n != 1 else ''}",
                model="rule-based-v1",
            ),
        )
        if self.signer:
            self.signer.sign(event)
        return event
