"""
SignedData CDS — Lottery Domain Models
Typed Pydantic payload schemas for lottery.brazil events.
"""

from __future__ import annotations

from pydantic import BaseModel

from cds.vocab import CDSVocab


class LotteryContentTypes:
    MEGA_SENA = CDSVocab.LOTTERY_MEGA_SENA
    LOTOFACIL = CDSVocab.LOTTERY_LOTOFACIL
    QUINA = CDSVocab.LOTTERY_QUINA
    LOTOMANIA = CDSVocab.LOTTERY_LOTOMANIA
    DUPLA_SENA = CDSVocab.LOTTERY_DUPLA_SENA


class PrizeTier(BaseModel):
    tier: int
    description: str
    winners: int
    prize_amount: float  # BRL per winner
    total_prize: float  # winners * prize_amount


class MegaSenaResult(BaseModel):
    concurso: int
    data_apuracao: str  # "29/03/2026"
    data_apuracao_iso: str  # "2026-03-29"
    local_sorteio: str = ""
    cidade_uf: str = ""
    dezenas: list[str]  # sorted: ["04","12","25","36","47","59"]
    dezenas_ordem_sorteio: list[str] = []  # draw order
    acumulado: bool
    premiacoes: list[PrizeTier] = []
    valor_arrecadado: float = 0
    valor_acumulado_proximo: float = 0
    data_proximo_concurso: str = ""
    concurso_anterior: int | None = None
    concurso_proximo: int | None = None

    @property
    def dezenas_formatted(self) -> str:
        return " \u00b7 ".join(self.dezenas)


class LotteryResult(BaseModel):
    """Generic lottery result for non-Mega-Sena games."""

    concurso: int
    data_apuracao: str
    data_apuracao_iso: str
    dezenas: list[str]
    acumulado: bool
    premiacoes: list[PrizeTier] = []
    valor_arrecadado: float = 0
    valor_acumulado_proximo: float = 0
