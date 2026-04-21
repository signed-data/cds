"""
CDS Python SDK — Core Schema v0.2.0
Every identity is a dereferenceable HTTP URI.
"""

from __future__ import annotations

import json
import uuid as _uuid_mod
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cds.vocab import CONTEXT_URI, EVENT_TYPE_URI, event_uri


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _new_uuid() -> str:
    return str(_uuid_mod.uuid4())


class SourceMeta(BaseModel):
    """
    A certified data source reference.
    `id` serialises as `@id` in JSON-LD output.

    Usage:
        from cds.vocab import CDSSources
        SourceMeta(id=CDSSources.CAIXA_LOTERIAS, fingerprint="sha256:...")
        # serialises to: { "@id": "https://...", "fingerprint": "sha256:..." }
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="@id")
    fingerprint: str | None = None

    @property
    def uri(self) -> str:
        return self.id


class ContextMeta(BaseModel):
    """LLM-generated context summary attached to a CDS event."""

    summary: str
    model: str = "rule-based-v1"
    generated_at: datetime = Field(default_factory=_now_utc)


class IntegrityMeta(BaseModel):
    """Cryptographic proof of a CDSEvent. `signed_by` is an HTTP URI."""

    hash: str  # "sha256:<hex>"
    signature: str  # base64 RSA-PSS
    signed_by: str  # URI — "https://signed-data.org"


class CDSEvent(BaseModel):
    """
    CDS event envelope v0.2.0 — Linked Data compliant.

    Usage:
        from cds.vocab import CDSVocab, CDSSources
        event = CDSEvent(
            content_type  = CDSVocab.LOTTERY_MEGA_SENA,
            source        = SourceMeta(id=CDSSources.CAIXA_LOTERIAS),
            occurred_at   = datetime.now(timezone.utc),
            lang          = "pt-BR",
            payload       = {"concurso": 2800},
            event_context = ContextMeta(summary="..."),
        )
        event.to_jsonld()  # → dict with @context, @type, @id
    """

    model_config = ConfigDict(populate_by_name=True)

    # Linked Data fields — serialise with @ prefix via aliases
    ld_context: str = Field(default=CONTEXT_URI, alias="@context")
    ld_type: str = Field(default=EVENT_TYPE_URI, alias="@type")
    ld_id: str = Field(default="", alias="@id")

    # Standard envelope
    spec_version: str = "0.2.0"
    id: str = Field(default_factory=_new_uuid)
    content_type: str  # URI — use CDSVocab constants
    source: SourceMeta
    occurred_at: datetime
    ingested_at: datetime = Field(default_factory=_now_utc)
    lang: str = "en"
    payload: dict[str, Any]
    event_context: ContextMeta | None = Field(default=None, alias="context")
    integrity: IntegrityMeta | None = None

    def model_post_init(self, __context: Any) -> None:
        if not self.ld_id:
            object.__setattr__(self, "ld_id", event_uri(self.id))

    def to_jsonld(self) -> dict[str, Any]:
        """Serialise to JSON-LD. @context/@type/@id appear first."""
        raw = self.model_dump(by_alias=True, mode="json")
        result: dict[str, Any] = {
            "@context": raw.pop("@context"),
            "@type": raw.pop("@type"),
            "@id": raw.pop("@id"),
        }
        result.update(raw)
        return result

    def canonical_bytes(self) -> bytes:
        """
        Deterministic UTF-8 JSON for signing.
        Includes @context, @type, @id.
        Excludes integrity and ingested_at.
        """
        data = self.model_dump(
            by_alias=True,
            mode="json",
            exclude={"integrity", "ingested_at"},
        )
        return json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")

    @classmethod
    def from_jsonld(cls, data: dict[str, Any]) -> CDSEvent:
        return cls.model_validate(data)

    @property
    def domain(self) -> str:
        """
        'https://signed-data.org/vocab/lottery-brazil/mega-sena-result'
        → 'lottery.brazil'
        """
        try:
            seg = self.content_type.split("/vocab/")[1]
            return seg.split("/")[0].replace("-", ".", 1)
        except (IndexError, AttributeError):
            return ""

    @property
    def event_type(self) -> str:
        """
        'https://signed-data.org/vocab/lottery-brazil/mega-sena-result'
        → 'mega-sena.result'
        Reverses the last hyphen to a dot (the original schema_name separator).
        """
        try:
            seg = self.content_type.split("/vocab/")[1]
            parts = seg.split("/")
            slug = parts[1] if len(parts) >= 2 else parts[0]
            # Reverse the LAST hyphen→dot (the original schema_name dot)
            idx = slug.rfind("-")
            if idx >= 0:
                return slug[:idx] + "." + slug[idx + 1 :]
            return slug
        except (IndexError, AttributeError):
            return ""
