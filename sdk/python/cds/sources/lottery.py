"""
SignedData CDS — Brazil Lottery Ingestor
Source: Caixa Econômica Federal public API (no auth required)

Endpoints:
    Latest:   GET /portaldeloterias/api/megasena/
    Specific: GET /portaldeloterias/api/megasena/{concurso}
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

import httpx

from cds.ingestor import BaseIngestor
from cds.schema import CDSEvent, ContextMeta, SourceMeta
from cds.sources.lottery_models import (
    LotteryContentTypes,
    MegaSenaResult,
    PrizeTier,
)
from cds.vocab import CDSSources

CAIXA_BASE = "https://servicebus2.caixa.gov.br/portaldeloterias/api"


def _parse_date_iso(br_date: str) -> str:
    parts = br_date.split("/")
    if len(parts) == 3:
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return br_date


def _brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _parse_premiacoes(raw: list[dict[str, Any]]) -> list[PrizeTier]:
    return [
        PrizeTier(
            tier=i + 1,
            description=item.get("descricao", f"Faixa {i + 1}"),
            winners=int(item.get("numeroDeGanhadores", 0)),
            prize_amount=float(item.get("valorPremio", 0)),
            total_prize=int(item.get("numeroDeGanhadores", 0)) * float(item.get("valorPremio", 0)),
        )
        for i, item in enumerate(raw)
    ]


def _build_summary(r: MegaSenaResult) -> str:
    dezenas = r.dezenas_formatted
    if r.acumulado:
        return (
            f"Mega Sena concurso {r.concurso} ({r.data_apuracao}): "
            f"ACUMULOU — dezenas: {dezenas}. "
            f"Próximo prêmio estimado: {_brl(r.valor_acumulado_proximo)} "
            f"em {r.data_proximo_concurso}."
        )
    tier1 = next((t for t in r.premiacoes if t.tier == 1), None)
    winners = tier1.winners if tier1 else 0
    prize = tier1.prize_amount if tier1 else 0
    plural = "ganhador" if winners == 1 else "ganhadores"
    return (
        f"Mega Sena concurso {r.concurso} ({r.data_apuracao}): "
        f"dezenas: {dezenas}. "
        f"{winners} {plural} da sena, prêmio de {_brl(prize)} cada."
    )


def _parse_response(raw: dict[str, Any]) -> MegaSenaResult:
    br_date = raw.get("dataApuracao", "")
    dezenas = sorted(raw.get("listaDezenas", []))
    return MegaSenaResult(
        concurso=int(raw.get("numero", 0)),
        data_apuracao=br_date,
        data_apuracao_iso=_parse_date_iso(br_date),
        local_sorteio=raw.get("localSorteio", ""),
        cidade_uf=raw.get("nomeMunicipiUFSorteio", ""),
        dezenas=dezenas,
        dezenas_ordem_sorteio=raw.get("listaDezenasOrdemSorteio", []),
        acumulado=bool(raw.get("acumulado", False)),
        premiacoes=_parse_premiacoes(raw.get("listaRateioPremio", [])),
        valor_arrecadado=float(raw.get("valorArrecadado", 0)),
        valor_acumulado_proximo=float(raw.get("valorEstimadoProximoConcurso", 0)),
        data_proximo_concurso=raw.get("dataProximoConcurso", ""),
        concurso_anterior=raw.get("numeroConcursoAnterior"),
        concurso_proximo=raw.get("numeroConcursoProximo"),
    )


class MegaSenaIngestor(BaseIngestor):
    content_type = LotteryContentTypes.MEGA_SENA

    def __init__(self, signer: Any, concursos: list[int] | None = None) -> None:
        super().__init__(signer)
        self.concursos = concursos

    async def fetch(self) -> list[CDSEvent]:
        targets: list[int | None] = list(self.concursos) if self.concursos else [None]
        events: list[CDSEvent] = []

        async with httpx.AsyncClient(timeout=15) as client:
            for concurso in targets:
                url = f"{CAIXA_BASE}/megasena/{concurso}" if concurso else f"{CAIXA_BASE}/megasena/"
                resp = await client.get(url, headers={"Accept": "application/json"})
                resp.raise_for_status()

                fp = "sha256:" + hashlib.sha256(resp.content).hexdigest()
                raw = resp.json()
                result = _parse_response(raw)

                try:
                    d, m, y = result.data_apuracao.split("/")
                    occurred = datetime.fromisoformat(f"{y}-{m}-{d}T21:00:00-03:00")
                except (ValueError, IndexError):
                    occurred = datetime.now(UTC)

                events.append(
                    CDSEvent(
                        content_type=LotteryContentTypes.MEGA_SENA,
                        source=SourceMeta(id=CDSSources.CAIXA_LOTERIAS, fingerprint=fp),
                        occurred_at=occurred,
                        lang="pt-BR",
                        payload=result.model_dump(mode="json"),
                        event_context=ContextMeta(
                            summary=_build_summary(result),
                            model="rule-based-v1",
                        ),
                    )
                )

        return events
