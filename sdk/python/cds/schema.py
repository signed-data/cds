"""
CDS Python SDK — Core Schema
Every identity is a dereferenceable HTTP URI.
"""

from __future__ import annotations

import base64
import json
import uuid as _uuid_mod
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cds.vocab import (
    CONTEXT_URI,
    EVENT_TYPE_URI,
    ISSUER_DID,
    VC20_CONTEXT,
    VC20_CRYPTOSUITE,
    event_uri,
)


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
    signature: str  # base64-encoded signature (RSA-PSS or ECDSA DER)
    signed_by: str  # URI — "https://signed-data.org"
    key_id: str | None = None  # verification key URI — "https://signed-data.org/keys/1"


class DataIntegrityProof(BaseModel):
    """W3C VC 2.0 Data Integrity Proof (ecdsa-rdfc-2022)."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = "DataIntegrityProof"
    cryptosuite: str = VC20_CRYPTOSUITE
    proof_purpose: str = Field(default="assertionMethod", alias="proofPurpose")
    verification_method: str = Field(..., alias="verificationMethod")
    created: datetime
    proof_value: str = Field(..., alias="proofValue")  # multibase base64url (u prefix)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, mode="json")


class CDSEvent(BaseModel):
    """
    CDS event envelope — Linked Data compliant.

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
        event.to_jsonld()    # → dict with @context, @type, @id  (v0.2.0 format)
        event.to_vc20()      # → W3C VC 2.0 VerifiableCredential dict
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

    # ── W3C VC 2.0 ───────────────────────────────────────────────────────────

    def to_vc20(self) -> dict[str, Any]:
        """Serialise as a W3C VC 2.0 VerifiableCredential JSON-LD document."""
        event_id = self.ld_id or event_uri(self.id)
        credential: dict[str, Any] = {
            "@context": [VC20_CONTEXT, CONTEXT_URI],
            "id": event_id,
            "type": ["VerifiableCredential", "CDSEvent"],
            "issuer": ISSUER_DID,
            "validFrom": self.ingested_at.isoformat(),
            "credentialSubject": {
                "@id": event_id + "#subject",
                "content_type": self.content_type,
                "spec_version": self.spec_version,
                "source": self.source.model_dump(by_alias=True, mode="json"),
                "occurred_at": self.occurred_at.isoformat(),
                "lang": self.lang,
                "payload": self.payload,
            },
        }
        if self.event_context:
            credential["credentialSubject"]["context"] = self.event_context.model_dump(mode="json")
        if self.integrity:
            sig_bytes = base64.b64decode(self.integrity.signature)
            proof_value = "u" + base64.urlsafe_b64encode(sig_bytes).rstrip(b"=").decode()
            credential["proof"] = {
                "type": "DataIntegrityProof",
                "cryptosuite": VC20_CRYPTOSUITE,
                "proofPurpose": "assertionMethod",
                "verificationMethod": self.integrity.key_id or "did:web:signed-data.org#key-1",
                "created": self.ingested_at.isoformat(),
                "proofValue": proof_value,
            }
        return credential

    def canonical_bytes_vc20(self) -> bytes:
        """Deterministic UTF-8 JSON of the VC 2.0 credential without proof, for signing."""
        doc = self.to_vc20()
        doc.pop("proof", None)
        return json.dumps(doc, sort_keys=True, ensure_ascii=False).encode("utf-8")

    @classmethod
    def from_vc20(cls, data: dict[str, Any]) -> CDSEvent:
        """Reconstruct a CDSEvent from a W3C VC 2.0 JSON-LD document."""
        subj = data["credentialSubject"]
        proof_data = data.get("proof")

        integrity: IntegrityMeta | None = None
        if proof_data and proof_data.get("type") == "DataIntegrityProof":
            pv = proof_data["proofValue"]
            if pv.startswith("u"):
                sig_bytes = base64.urlsafe_b64decode(pv[1:] + "==")
                signature = base64.b64encode(sig_bytes).decode()
            else:
                signature = pv
            vm = proof_data.get("verificationMethod", "")
            integrity = IntegrityMeta(
                hash="",
                signature=signature,
                signed_by=vm.split("#")[0] if "#" in vm else vm,
                key_id=vm or None,
            )

        event_id_uri = data.get("id", "")
        uuid_part = (
            event_id_uri.split("/events/")[-1] if "/events/" in event_id_uri else _new_uuid()
        )

        return cls.model_validate({
            "@context": CONTEXT_URI,
            "@type": EVENT_TYPE_URI,
            "@id": event_id_uri,
            "spec_version": subj.get("spec_version", "0.3.0"),
            "id": uuid_part,
            "content_type": subj["content_type"],
            "source": subj["source"],
            "occurred_at": subj["occurred_at"],
            "ingested_at": data.get("validFrom"),
            "lang": subj.get("lang", "en"),
            "payload": subj.get("payload", {}),
            "context": subj.get("context"),
            "integrity": integrity.model_dump() if integrity else None,
        })

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
