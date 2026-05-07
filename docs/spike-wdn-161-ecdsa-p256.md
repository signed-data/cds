# Spike: Python VC Library for ecdsa-rdfc-2022 (WDN-161)

## Conclusion

**Use the `cryptography` library directly. Do not add pyvckit.**

## Evaluation

### pyvckit
- Supports Ed25519 only (eddsa-rdfc-2022 cryptosuite)
- Does NOT support ECDSA P-256 (ecdsa-rdfc-2022)
- Heavy dependency tree (55 packages including fonttools, reportlab, pynacl)
- Verdict: **rejected** — wrong curve, wrong weight class

### vc-api-py
- Thin wrapper, unmaintained, no P-256 support
- Verdict: **rejected**

### Direct implementation with `cryptography` (chosen)
- `cryptography` is already a first-class dep of the CDS SDK
- Supports ECDSA P-256 via `ec.generate_private_key(SECP256R1())`
- Uses RFC 6979 deterministic nonce by default (no randomness required)
- Signing: `key.sign(data, ECDSA(SHA256()))` — DER-encoded output
- Verification: `key.verify(sig, data, ECDSA(SHA256()))`
- No new dependencies

## Key format decisions

| Concern | Decision |
|---|---|
| Key type | ECDSA P-256 (secp256r1 / prime256v1) |
| Signature algorithm | ECDSA with SHA-256, RFC 6979 nonce |
| Signature encoding | Base64 DER (same field as RSA signature in IntegrityMeta) |
| Key document format | W3C Multikey at `https://signed-data.org/keys/1` |
| Public key encoding | multibase base58btc, multicodec prefix 0x1200 (p256-pub) |

## ecdsa-rdfc-2022 note

Full ecdsa-rdfc-2022 (W3C Data Integrity spec) requires URDNA2015 RDF normalization
before signing. The CDS SDK's current signing targets JSON payloads, not full
JSON-LD documents, so URDNA2015 is not needed for the v0.3.0 CDS signing layer.
Future WDN tickets tracking full VC 2.0 compliance (WDN-160 epic) can add
pyld/rdflib for normalization when needed.

## Implementation delivered

- `sdk/python/cds/signer.py` — CDSSigner and CDSVerifier auto-detect RSA vs ECDSA P-256
- `sdk/python/cds/schema.py` — IntegrityMeta.key_id field added (nullable, backward-compatible)
- `scripts/gen-ecdsa-p256-keypair.py` — keygen + Multikey document generator
- `keys/1.json` — Multikey document template (publicKeyMultibase to be filled after provisioning)
