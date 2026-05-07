"""
SignedData CDS — Integrity Brazil Domain Models
Typed Pydantic payload schemas for integrity.brazil events.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from cds.vocab import CDSVocab


class IntegrityContentTypes:
    SANCTIONS_CONSOLIDATED = CDSVocab.INTEGRITY_SANCTIONS_CONSOLIDATED
    SANCTIONS_CEIS         = CDSVocab.INTEGRITY_SANCTIONS_CEIS
    SANCTIONS_CNEP         = CDSVocab.INTEGRITY_SANCTIONS_CNEP
    SANCTIONS_CEPIM        = CDSVocab.INTEGRITY_SANCTIONS_CEPIM


class SanctionRecord(BaseModel):
    """A single federal sanction record from CEIS, CNEP, or CEPIM.

    Normalised surface is the contract; the verbatim upstream record is
    preserved under `raw` so future tools can access fields we do not yet
    expose (and so schema drift does not break the normalised surface).
    """
    registry:          Literal["CEIS", "CNEP", "CEPIM"]
    cnpj:              str
    nome_sancionado:   str
    sanction_type:     str | None = None
    start_date:        str | None = None
    end_date:          str | None = None
    sanctioning_organ: str | None = None
    legal_basis:       str | None = None
    raw:               dict[str, Any]


class SanctionsConsolidated(BaseModel):
    """Payload for integrity.brazil/sanctions.consolidated.

    Merges CEIS, CNEP, and CEPIM lookups for one CNPJ into a single signed
    event.
    """
    cnpj:            str   # bare digits: "33000167000101"
    cnpj_formatted:  str   # "33.000.167/0001-01"
    sanction_found:  bool
    sanction_count:  int
    registries:      dict[str, list[SanctionRecord]]  # keys: ceis, cnep, cepim
    query_timestamp: str

    @property
    def is_clean(self) -> bool:
        return not self.sanction_found
