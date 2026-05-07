# Signing algorithm

CDS uses RSA-PSS with SHA-256. This document describes the algorithm in
full so that anyone can implement a conformant signer or verifier without
reading the source code.

---

## Key requirements

| Property | Value |
|---|---|
| Algorithm | RSA-PSS |
| Key size | 4096 bits minimum |
| Hash | SHA-256 |
| MGF | MGF1 with SHA-256 |
| Salt length | Maximum (PSS.MAX_LENGTH) |
| Key format | PKCS#8 PEM (private), SubjectPublicKeyInfo PEM (public) |

---

## Canonical serialisation

The input to the signing function is the **canonical JSON** of the event.

**Rules:**
1. Serialise the event as JSON with keys sorted alphabetically (`sort_keys=True`)
2. Encode as UTF-8 bytes (no BOM)
3. **Exclude** the `integrity` field entirely
4. **Exclude** the `ingested_at` field entirely
5. No trailing newline, no extra whitespace

`ingested_at` is excluded because it is set at ingestion time and may differ
between the producer and a re-ingestion. `integrity` is excluded because it
contains the signature itself.

**Python reference:**
```python
import json

def canonical_bytes(event: CDSEvent) -> bytes:
    data = event.model_dump(
        exclude={"integrity", "ingested_at"},
        mode="json",
    )
    return json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
```

**TypeScript reference:**
```typescript
canonicalBytes(): Buffer {
  const { integrity: _i, ingested_at: _ia, ...rest } = this.toJSON();
  const sorted = Object.fromEntries(
    Object.entries(rest).sort(([a], [b]) => a.localeCompare(b))
  );
  return Buffer.from(JSON.stringify(sorted), "utf-8");
}
```

---

## Signing (producer)

```python
import hashlib, base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

canonical = event.canonical_bytes()

# 1. Hash
hash_hex = hashlib.sha256(canonical).hexdigest()
payload_hash = f"sha256:{hash_hex}"

# 2. Sign
raw_signature = private_key.sign(
    canonical,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH,
    ),
    hashes.SHA256(),
)

# 3. Attach
event.integrity = IntegrityMeta(
    hash      = payload_hash,
    signature = base64.b64encode(raw_signature).decode(),
    signed_by = issuer,
)
```

---

## Verification (consumer)

```python
import hashlib, base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

if not event.integrity:
    raise ValueError("Event has no integrity metadata.")

canonical = event.canonical_bytes()

# 1. Check hash
expected = "sha256:" + hashlib.sha256(canonical).hexdigest()
if expected != event.integrity.hash:
    raise ValueError(f"Hash mismatch. Expected {expected}, got {event.integrity.hash}")

# 2. Verify signature
raw_signature = base64.b64decode(event.integrity.signature)
public_key.verify(
    raw_signature,
    canonical,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH,
    ),
    hashes.SHA256(),
)
# Raises cryptography.exceptions.InvalidSignature on failure
```

---

## Why RSA-PSS and not ECDSA or Ed25519?

CDS chose RSA-4096 PSS for conservatism and compatibility:

- **Broad support:** RSA-PSS is supported natively in Python's `cryptography`,
  Node.js `crypto`, AWS KMS, Azure Key Vault, and every HSM on the market.
- **FIPS compliance:** Required by some enterprise consumers.
- **No curve selection politics:** ECDSA curve choice (P-256 vs secp256k1) is
  contentious. RSA avoids it.

The tradeoff is key size (4096-bit RSA = 512-byte signatures vs 64 bytes for Ed25519).
For data feeds where signatures are attached to JSON events, this is acceptable.

A future spec version (v0.2.0) will add Ed25519 as an optional algorithm.
RSA-PSS SHA-256 will remain the required minimum.

---

## Integrity metadata fields

```json
{
  "hash":      "sha256:a1b2c3d4...",
  "signature": "MX6rj3qK...",
  "signed_by": "signed-data.org"
}
```

| Field | Description |
|---|---|
| `hash` | `"sha256:" + hex(SHA256(canonical_bytes))` |
| `signature` | `base64(RSA-PSS-sign(canonical_bytes, private_key))` |
| `signed_by` | Issuer identifier — typically a domain name |

The `hash` field is redundant with the signature (a valid signature implies
the hash is correct) but is included for fast rejection before signature
verification, which is computationally expensive.

---

## Key distribution

The issuer SHOULD publish their public key at:

```
https://{issuer}/.well-known/cds-public-key.pem
```

For `signed-data.org`:
```
https://signed-data.org/.well-known/cds-public-key.pem
```

This follows the same convention as DKIM, ACME, and other well-known URI schemes.
