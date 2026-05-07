"""
SignedData CDS — CEP Brazil Fetcher
Sources:
  BrasilAPI CEP v2 — https://brasilapi.com.br/api/cep/v2/{cep}
  ViaCEP — https://viacep.com.br/ws/{UF}/{city}/{street}/json/

Query-driven: no scheduled ingestor. Called per lookup from the MCP server.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

import httpx

from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.vocab import CDSSources, CDSVocab

BRASILAPI_CEP_BASE = "https://brasilapi.com.br/api/cep/v2"
VIACEP_BASE = "https://viacep.com.br/ws"


def _fingerprint(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def validate_cep(cep: str) -> str:
    """Validate and normalise a CEP. Returns bare 8-digit string or raises ValueError."""
    bare = re.sub(r"[-\s]", "", cep.strip())
    if not re.fullmatch(r"\d{8}", bare):
        raise ValueError(f"CEP must have 8 digits, got: {cep!r}")
    return bare


def format_cep(bare: str) -> str:
    """'01001001' → '01001-001'"""
    return f"{bare[:5]}-{bare[5:]}"


class CEPFetcher:
    """Fetches and signs CEP data on demand."""

    def __init__(self, signer: Any = None) -> None:
        self.signer = signer

    async def fetch_address(self, cep: str) -> CDSEvent:
        """Fetch address for a CEP via BrasilAPI CEP v2."""
        bare = validate_cep(cep)

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{BRASILAPI_CEP_BASE}/{bare}")
            resp.raise_for_status()
            fp = _fingerprint(resp.content)
            data = resp.json()

        payload = {
            "cep": bare,
            "cep_formatted": format_cep(bare),
            "street": data.get("street") or "",
            "neighborhood": data.get("neighborhood") or "",
            "city": data.get("city") or "",
            "state": data.get("state") or "",
        }
        location_str = (
            f"{payload['street']}, {payload['neighborhood']}, "
            f"{payload['city']}/{payload['state']}"
        )

        event = CDSEvent(
            content_type=CDSVocab.LOCATION_CEP_ADDRESS,
            source=SourceMeta(id=CDSSources.BRASILAPI, fingerprint=fp),
            occurred_at=datetime.now(UTC),
            lang="pt-BR",
            payload=payload,
            event_context=ContextMeta(
                summary=f"CEP {format_cep(bare)}: {location_str}",
                model="rule-based-v1",
            ),
        )
        if self.signer:
            self.signer.sign(event)
        return event

    async def search_by_address(
        self,
        logradouro: str,
        municipio: str,
        uf: str,
    ) -> CDSEvent:
        """Search CEPs by address components via ViaCEP."""
        url = f"{VIACEP_BASE}/{uf.upper()}/{municipio}/{logradouro}/json/"

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            fp = _fingerprint(resp.content)
            data = resp.json()

        items = data if isinstance(data, list) else []
        results = [
            {
                "cep": item.get("cep", "").replace("-", ""),
                "cep_formatted": item.get("cep", ""),
                "street": item.get("logradouro", ""),
                "neighborhood": item.get("bairro", ""),
                "city": item.get("localidade", ""),
                "state": item.get("uf", ""),
            }
            for item in items
        ]

        event = CDSEvent(
            content_type=CDSVocab.LOCATION_CEP_SEARCH,
            source=SourceMeta(id=CDSSources.VIACEP, fingerprint=fp),
            occurred_at=datetime.now(UTC),
            lang="pt-BR",
            payload={
                "query": {"logradouro": logradouro, "municipio": municipio, "uf": uf},
                "results": results,
                "count": len(results),
            },
            event_context=ContextMeta(
                summary=f"CEP search: {logradouro}, {municipio}/{uf} — {len(results)} result(s)",
                model="rule-based-v1",
            ),
        )
        if self.signer:
            self.signer.sign(event)
        return event
