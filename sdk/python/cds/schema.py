"""
SignedData CDS — Core Schema
Python 3.12+.  Issuer: signed-data.org
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(UTC)


def _uuid() -> str:
    return str(uuid.uuid4())


class SourceMeta(BaseModel):
    id: str
    fingerprint: str | None = None


class ContextMeta(BaseModel):
    summary: str
    model: str = "rule-based-v1"
    generated_at: datetime = Field(default_factory=_now)


class IntegrityMeta(BaseModel):
    hash: str        # sha256 of canonical payload
    signature: str   # base64 RSA-PSS
    signed_by: str   # issuer e.g. "signed-data.org"


class CDSContentType(BaseModel):
    """
    Semantic MIME type for CDS events.

    Wire format:  application/vnd.cds.{domain}.{schema}+json;v={version}
    Examples:
        CDSContentType(domain="weather",         schema_name="forecast.current")
        CDSContentType(domain="sports.football", schema_name="match.result")
    """
    domain: str
    schema_name: str
    version: str = "1"
    encoding: str = "json"

    @property
    def mime_type(self) -> str:
        d = self.domain.replace(".", "-")
        s = self.schema_name.replace(".", "-")
        return f"application/vnd.cds.{d}.{s}+{self.encoding};v={self.version}"

    def __str__(self) -> str:
        return self.mime_type


class CDSEvent(BaseModel):
    """
    CDS aggregate root — immutable once signed.
    The canonical envelope for any signed, curated real-time event.
    """
    spec_version: str = "0.1.0"
    id: str = Field(default_factory=_uuid)
    content_type: CDSContentType
    source: SourceMeta
    occurred_at: datetime
    ingested_at: datetime = Field(default_factory=_now)
    lang: str = "en"
    payload: dict[str, Any]
    context: ContextMeta | None = None
    integrity: IntegrityMeta | None = None

    def canonical_bytes(self) -> bytes:
        """Deterministic serialisation for signing — excludes integrity + ingested_at."""
        import json
        data = self.model_dump(exclude={"integrity", "ingested_at"}, mode="json")
        return json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")

    @property
    def domain(self) -> str:
        return self.content_type.domain

    @property
    def event_type(self) -> str:
        return self.content_type.schema_name
