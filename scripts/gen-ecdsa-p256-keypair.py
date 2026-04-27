#!/usr/bin/env python3
"""
Generate an ECDSA P-256 keypair for CDS signing (v0.3.0).

Outputs:
  - Private key PEM  → store in Secrets Manager as cds/signing-private-key-ecdsa-v1
  - Public key PEM   → informational / backup
  - Multikey document → publish at signed-data.org/keys/1

Multicodec prefix for p256-pub: 0x1200 (varint encoded: 0x80, 0x24)
Encoding: multibase base58btc (z prefix)

Usage:
    python3 scripts/gen-ecdsa-p256-keypair.py
"""
from __future__ import annotations

import base64
import json
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ec import (
    SECP256R1,
    EllipticCurvePublicKey,
    generate_private_key,
)


# ── Multibase base58btc (Bitcoin alphabet) ──────────────────

_B58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _b58encode(data: bytes) -> str:
    """Encode bytes as base58btc (no checksum)."""
    n = int.from_bytes(data, "big")
    result = []
    while n:
        n, r = divmod(n, 58)
        result.append(_B58_ALPHABET[r : r + 1])
    # leading zero bytes → leading '1's
    for byte in data:
        if byte == 0:
            result.append(b"1")
        else:
            break
    return b"".join(reversed(result)).decode("ascii")


def _multibase_b58btc(data: bytes) -> str:
    """Encode as multibase base58btc (prefix 'z')."""
    return "z" + _b58encode(data)


# ── Multikey encoding for P-256 ─────────────────────────────
# p256-pub multicodec = 0x1200  →  varint = [0x80, 0x24]
_P256_PUB_MULTICODEC = bytes([0x80, 0x24])


def public_key_to_multikey(pub: EllipticCurvePublicKey) -> str:
    """Encode a P-256 public key as a Multikey multibase string."""
    compressed = pub.public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.CompressedPoint,
    )
    return _multibase_b58btc(_P256_PUB_MULTICODEC + compressed)


# ── Main ────────────────────────────────────────────────────

def main() -> None:
    private_key = generate_private_key(SECP256R1())

    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ).decode()

    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    public_key_multibase = public_key_to_multikey(private_key.public_key())

    multikey_doc = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://w3id.org/security/multikey/v1",
        ],
        "id": "https://signed-data.org/keys/1",
        "type": "Multikey",
        "controller": "https://signed-data.org",
        "publicKeyMultibase": public_key_multibase,
    }

    sep = "=" * 72

    print(sep)
    print("PRIVATE KEY PEM — store in Secrets Manager as cds/signing-private-key-ecdsa-v1")
    print(sep)
    print(private_pem)

    print(sep)
    print("PUBLIC KEY PEM — informational backup")
    print(sep)
    print(public_pem)

    print(sep)
    print("MULTIKEY DOCUMENT — publish at https://signed-data.org/keys/1")
    print(sep)
    print(json.dumps(multikey_doc, indent=2))
    print()

    print(sep)
    print("AWS CLI — provision the secret (run once):")
    print(sep)
    print("aws secretsmanager create-secret \\")
    print("  --name cds/signing-private-key-ecdsa-v1 \\")
    print("  --secret-string $'<PASTE PRIVATE KEY PEM HERE>' \\")
    print("  --region us-east-1")
    print()
    print("publicKeyMultibase:", public_key_multibase)


if __name__ == "__main__":
    main()
