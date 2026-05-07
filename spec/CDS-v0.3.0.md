# CDS v0.3.0 — W3C Verifiable Credentials 2.0 Profile

**Status:** Draft  
**Date:** 2026-04-27  
**Authors:** signed-data.org

---

## 1. Overview

CDS v0.3.0 defines a **W3C Verifiable Credentials 2.0 profile** for CDS events.

Every CDS event can now be serialised as a conforming `VerifiableCredential` document, making it directly processable by any W3C VC 2.0 toolchain — wallets, verifiers, credential registries, and AI agent frameworks that consume linked credentials.

The internal signing algorithm does not change. What changes is the envelope shape: the custom `integrity` proof is replaced by a standard `DataIntegrityProof`, and the event body moves into `credentialSubject`.

---

## 2. Credential Structure

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://signed-data.org/contexts/cds/v1.jsonld"
  ],
  "id": "https://signed-data.org/events/3f8a2d1c-...",
  "type": ["VerifiableCredential", "CDSEvent"],
  "issuer": "did:web:signed-data.org",
  "validFrom": "2026-04-27T14:00:00+00:00",
  "credentialSubject": {
    "@id": "https://signed-data.org/events/3f8a2d1c-...#subject",
    "content_type": "https://signed-data.org/vocab/lottery-brazil/mega-sena-result",
    "spec_version": "0.3.0",
    "source": {
      "@id": "https://signed-data.org/sources/caixa.gov.br.loterias.v1"
    },
    "occurred_at": "2026-04-27T21:00:00+00:00",
    "lang": "pt-BR",
    "payload": {
      "concurso": 2800,
      "dezenas": ["05", "10", "20", "30", "40", "50"]
    }
  },
  "proof": {
    "type": "DataIntegrityProof",
    "cryptosuite": "ecdsa-rdfc-2022",
    "proofPurpose": "assertionMethod",
    "verificationMethod": "did:web:signed-data.org#key-1",
    "created": "2026-04-27T14:00:00+00:00",
    "proofValue": "uMEYCIQD..."
  }
}
```

---

## 3. Field Mapping

| VC 2.0 field | CDS source | Notes |
|---|---|---|
| `@context[0]` | fixed | `https://www.w3.org/ns/credentials/v2` |
| `@context[1]` | fixed | `https://signed-data.org/contexts/cds/v1.jsonld` |
| `id` | `event_uri(event.id)` | `https://signed-data.org/events/{uuid}` |
| `type` | fixed | `["VerifiableCredential", "CDSEvent"]` |
| `issuer` | fixed | `did:web:signed-data.org` |
| `validFrom` | `event.ingested_at` | ISO 8601 UTC |
| `credentialSubject.@id` | `event_uri(event.id) + "#subject"` | fragment URI |
| `credentialSubject.content_type` | `event.content_type` | vocabulary URI |
| `credentialSubject.spec_version` | `event.spec_version` | `"0.3.0"` |
| `credentialSubject.source.@id` | `event.source.id` | source URI |
| `credentialSubject.occurred_at` | `event.occurred_at` | ISO 8601 UTC |
| `credentialSubject.lang` | `event.lang` | BCP-47 language tag |
| `credentialSubject.payload` | `event.payload` | domain-specific data |
| `proof.type` | fixed | `"DataIntegrityProof"` |
| `proof.cryptosuite` | fixed | `"ecdsa-rdfc-2022"` |
| `proof.proofPurpose` | fixed | `"assertionMethod"` |
| `proof.verificationMethod` | `event.integrity.key_id` | defaults to `did:web:signed-data.org#key-1` |
| `proof.created` | `event.ingested_at` | ISO 8601 UTC |
| `proof.proofValue` | ECDSA P-256 signature | multibase base64url-no-pad (`u` prefix) |

---

## 4. Canonicalization and Signing

CDS v0.3.0 uses a simplified canonicalization: the credential document (without `proof`) is serialised as deterministic UTF-8 JSON with `sort_keys=True`, then signed with ECDSA P-256 SHA-256.

The `proofValue` is the raw DER-encoded ECDSA signature encoded as multibase base64url-no-pad (`u` prefix as defined in [Multibase](https://www.w3.org/TR/vc-data-integrity/#multibase-0)):

```
proofValue = "u" + base64url-no-pad(DER(ECDSA-P256-Sign(SHA256(canonical_json))))
```

Note: Full RDF Dataset Canonicalization (RDNA/URDNA2015) as specified by `ecdsa-rdfc-2022` is planned for v0.4.0. The current implementation uses JSON sort-key canonicalization and labels the cryptosuite accordingly in documentation.

---

## 5. Verification

To verify a CDS v0.3.0 credential:

1. Extract and strip the `proof` field.
2. Serialise the remaining document as deterministic UTF-8 JSON with `sort_keys=True`.
3. Decode `proof.proofValue`: strip the `u` prefix, base64url-decode (add `==` padding as needed).
4. Verify the DER-encoded ECDSA P-256 signature over the canonical bytes using the public key at `proof.verificationMethod`.
5. Confirm `proof.verificationMethod` resolves to a key published at `did:web:signed-data.org`.

---

## 6. Python SDK

```python
from cds.signer import CDSSigner, CDSVerifier
from cds.schema import CDSEvent, SourceMeta
from cds.vocab import CDSVocab, CDSSources

# Sign → VC 2.0
signer = CDSSigner("keys/ecdsa-private.pem")
event = CDSEvent(
    content_type=CDSVocab.LOTTERY_MEGA_SENA,
    source=SourceMeta(**{"@id": CDSSources.CAIXA_LOTERIAS}),
    occurred_at=datetime.now(UTC),
    lang="pt-BR",
    payload={"concurso": 2800},
)
vc = signer.sign_vc20(event)   # → dict (W3C VC 2.0)

# Verify
verifier = CDSVerifier("keys/ecdsa-public.pem")
verifier.verify_vc20(vc)       # raises on any failure

# Reconstruct CDSEvent from VC 2.0
restored = CDSEvent.from_vc20(vc)
```

---

## 7. DID Document

The issuer DID `did:web:signed-data.org` resolves to `https://signed-data.org/.well-known/did.json`.

The `#key-1` verification method references the ECDSA P-256 public key in JWK format.

---

## 8. Backwards Compatibility

CDS v0.3.0 is additive. All v0.2.0 events remain valid. The new `to_vc20()` and `from_vc20()` methods coexist with `to_jsonld()` and `from_jsonld()`. The `sign()` method is unchanged; `sign_vc20()` is new.

The v0.2.0 `integrity` field (custom proof format) is preserved for backwards compatibility and populated by `sign()`.

---

## 9. Roadmap

- **v0.3.0** (this): VC 2.0 envelope, `DataIntegrityProof`, Python SDK `to_vc20`/`from_vc20`/`sign_vc20`/`verify_vc20`
- **v0.4.0**: `credentialStatus` for revocation via Status List 2021; TypeScript SDK parity
- **v0.5.0**: Full RDNA canonicalization (URDNA2015) for true `ecdsa-rdfc-2022` conformance
