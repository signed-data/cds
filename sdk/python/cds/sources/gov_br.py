"""
SignedData CDS — Government Brazil Fetcher (government.brazil)
Source: Portal da Transparência — https://api.portaldatransparencia.gov.br/api-de-dados

Query-driven: no scheduled ingestor. Called per CNPJ lookup from the MCP server.
Phase 1 fetches CEIS (empresas inidôneas) and CNEP (Lei Anticorrupção) in parallel.
"""
from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, datetime
from typing import Any

import httpx

from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.sources.companies import _format_cnpj, validate_cnpj
from cds.sources.gov_br_models import (
    GovBrContentTypes,
    SanctionRecord,
    SanctionsConsolidated,
)
from cds.vocab import CDSSources

PORTAL_TRANSPARENCIA_BASE = "https://api.portaldatransparencia.gov.br/api-de-dados"
TOKEN_HEADER = "chave-api-dados"


def _fingerprint(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _nested_get(raw: dict[str, Any], *keys: str) -> str | None:
    """Safe nested dict traversal returning the final string or None."""
    cur: Any = raw
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
        if cur is None:
            return None
    return str(cur) if cur is not None else None


def _normalise_ceis(raw: dict[str, Any]) -> SanctionRecord:
    return SanctionRecord(
        registry="CEIS",
        cnpj=str(raw.get("cnpjSancionado") or "").strip(),
        nome_sancionado=str(raw.get("nomeSancionado") or raw.get("razaoSocial") or "").strip(),
        sanction_type=_nested_get(raw, "tipoSancao", "descricao"),
        start_date=raw.get("dataInicioSancao"),
        end_date=raw.get("dataFimSancao"),
        sanctioning_organ=_nested_get(raw, "orgaoSancionador", "nome"),
        legal_basis=raw.get("fundamentacao"),
        raw=raw,
    )


def _normalise_cnep(raw: dict[str, Any]) -> SanctionRecord:
    return SanctionRecord(
        registry="CNEP",
        cnpj=str(raw.get("cnpjSancionado") or "").strip(),
        nome_sancionado=str(raw.get("nomeSancionado") or raw.get("razaoSocial") or "").strip(),
        sanction_type=_nested_get(raw, "tipoSancao", "descricao"),
        start_date=raw.get("dataInicioSancao"),
        end_date=raw.get("dataFimSancao"),
        sanctioning_organ=_nested_get(raw, "orgaoSancionador", "nome"),
        legal_basis=raw.get("fundamentacao"),
        raw=raw,
    )


def _parse_consolidated(
    cnpj_bare: str,
    query_ts: str,
    ceis_raw: list[dict[str, Any]],
    cnep_raw: list[dict[str, Any]],
) -> SanctionsConsolidated:
    ceis = [_normalise_ceis(r) for r in ceis_raw]
    cnep = [_normalise_cnep(r) for r in cnep_raw]
    total = len(ceis) + len(cnep)
    return SanctionsConsolidated(
        cnpj=cnpj_bare,
        cnpj_formatted=_format_cnpj(cnpj_bare),
        sanction_found=total > 0,
        sanction_count=total,
        registries={"ceis": ceis, "cnep": cnep},
        query_timestamp=query_ts,
    )


def _build_summary(consolidated: SanctionsConsolidated) -> str:
    cnpj = consolidated.cnpj_formatted
    if not consolidated.sanction_found:
        return f"{cnpj}: sem sanções federais em CEIS ou CNEP."
    breakdown = []
    for key in ("ceis", "cnep"):
        count = len(consolidated.registries.get(key, []))
        if count:
            breakdown.append(f"{count} em {key.upper()}")
    total = consolidated.sanction_count
    plural = "ões" if total != 1 else "ão"
    return f"{cnpj}: {total} sanç{plural} ativa(s): " + ", ".join(breakdown) + "."


class MissingTokenError(RuntimeError):
    """Raised when the Portal da Transparência token is not configured."""


class SanctionsFetcher:
    """
    Fetches and signs CEIS/CNEP sanction data on demand.
    Not a scheduled ingestor — called per CNPJ query from the MCP server.
    """

    def __init__(self, token: str, signer: Any = None) -> None:
        if not token:
            raise MissingTokenError(
                "Portal da Transparência token is required. "
                "Set PORTAL_TRANSPARENCIA_TOKEN env var or pass token=."
            )
        self.token = token
        self.signer = signer

    async def fetch_consolidated(self, cnpj: str) -> CDSEvent:
        """Fetch consolidated sanction status (CEIS + CNEP) for a CNPJ.

        Validates CNPJ check digits before the API call. Raises ValueError for
        invalid CNPJ and httpx.HTTPStatusError on upstream error. A partial
        upstream failure (e.g. CEIS 200 but CNEP 503) fails the whole call.
        """
        bare = validate_cnpj(cnpj)
        query_ts = datetime.now(UTC).isoformat()

        headers = {TOKEN_HEADER: self.token, "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            ceis_resp, cnep_resp = await asyncio.gather(
                client.get(
                    f"{PORTAL_TRANSPARENCIA_BASE}/ceis",
                    params={"cnpjSancionado": bare, "pagina": 1},
                ),
                client.get(
                    f"{PORTAL_TRANSPARENCIA_BASE}/cnep",
                    params={"cnpjSancionado": bare, "pagina": 1},
                ),
            )
        for resp in (ceis_resp, cnep_resp):
            resp.raise_for_status()

        consolidated = _parse_consolidated(
            bare, query_ts, ceis_resp.json(), cnep_resp.json()
        )
        fingerprint = _fingerprint(ceis_resp.content + cnep_resp.content)

        event = CDSEvent(
            content_type=GovBrContentTypes.SANCTIONS_CONSOLIDATED,
            source=SourceMeta(id=CDSSources.PORTAL_TRANSPARENCIA, fingerprint=fingerprint),
            occurred_at=datetime.now(UTC),
            lang="pt-BR",
            payload=consolidated.model_dump(mode="json"),
            event_context=ContextMeta(
                summary=_build_summary(consolidated),
                model="rule-based-v1",
            ),
        )
        if self.signer:
            self.signer.sign(event)
        return event
