"""
SignedData CDS — Government Brazil Domain Models (government.brazil)
Typed Pydantic payload schemas for government.brazil sanctions events.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from cds.vocab import CDSVocab


class GovBrContentTypes:
    SANCTIONS_CONSOLIDATED = CDSVocab.GOV_BR_SANCTIONS_CONSOLIDATED
    SANCTIONS_CEIS         = CDSVocab.GOV_BR_SANCTIONS_CEIS
    SANCTIONS_CNEP         = CDSVocab.GOV_BR_SANCTIONS_CNEP


class SanctionRecord(BaseModel):
    """A single federal sanction record from CEIS or CNEP.

    Normalised surface is the contract; the verbatim upstream record is
    preserved under `raw` so future tools can access fields not yet exposed
    and so upstream schema drift does not break the normalised surface.
    """
    registry:          Literal["CEIS", "CNEP"]
    cnpj:              str
    nome_sancionado:   str
    sanction_type:     str | None = None
    start_date:        str | None = None
    end_date:          str | None = None
    sanctioning_organ: str | None = None
    legal_basis:       str | None = None
    raw:               dict[str, Any]


class SanctionsConsolidated(BaseModel):
    """Payload for government.brazil/sanctions.consolidated.

    Merges CEIS and CNEP lookups for one CNPJ into a single signed event.
    """
    cnpj:            str   # bare digits: "33000167000101"
    cnpj_formatted:  str   # "33.000.167/0001-01"
    sanction_found:  bool
    sanction_count:  int
    registries:      dict[str, list[SanctionRecord]]  # keys: ceis, cnep
    query_timestamp: str

    @property
    def is_clean(self) -> bool:
        return not self.sanction_found
