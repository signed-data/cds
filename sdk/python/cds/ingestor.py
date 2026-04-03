"""
SignedData CDS — Base Ingestor
All data-source adapters extend BaseIngestor.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from cds.schema import CDSEvent
from cds.signer import CDSSigner


class BaseIngestor(ABC):
    content_type: str   # URI — declared by each subclass

    def __init__(self, signer: CDSSigner) -> None:
        self.signer = signer

    @abstractmethod
    async def fetch(self) -> list[CDSEvent]:
        """Fetch raw data from source and return unsigned CDSEvents."""
        ...

    async def ingest(self) -> list[CDSEvent]:
        """Fetch + sign.  This is what callers use."""
        return [self.signer.sign(e) for e in await self.fetch()]
