"""
SignedData CDS — Signer & Verifier

Supports two key types detected automatically from the PEM:
  - RSA-4096 PSS SHA-256  (v0.2.x keys — cds/signing-private-key)
  - ECDSA P-256 SHA-256   (v0.3.0 keys — cds/signing-private-key-ecdsa-v1)

ECDSA uses RFC 6979 deterministic nonce (Python cryptography default).
"""

from __future__ import annotations

import base64
import hashlib
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.asymmetric.ec import (
    ECDSA,
    SECP256R1,
    EllipticCurvePrivateKey,
    EllipticCurvePublicKey,
)
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from cds.schema import CDSEvent, DataIntegrityProof, IntegrityMeta
from cds.vocab import VERIFICATION_METHOD_KEY1

# ── RSA signing params ───────────────────────────────────────

_PSS = padding.PSS(
    mgf=padding.MGF1(hashes.SHA256()),
    salt_length=padding.PSS.MAX_LENGTH,
)

# ── Key URI for new ECDSA keys (published at signed-data.org) ─

KEY_URI_ECDSA_V1 = "https://signed-data.org/keys/1"
KEY_URI_RSA_V0   = "https://signed-data.org/keys/0"


# ── Loaders ──────────────────────────────────────────────────

def _read_pem(path_or_pem: str) -> bytes:
    if path_or_pem.startswith("-----"):
        return path_or_pem.encode()
    with open(path_or_pem, "rb") as f:
        return f.read()


def _load_private(path_or_pem: str) -> RSAPrivateKey | EllipticCurvePrivateKey:
    return serialization.load_pem_private_key(_read_pem(path_or_pem), password=None)  # type: ignore[return-value]


def _load_public(path_or_pem: str) -> RSAPublicKey | EllipticCurvePublicKey:
    return serialization.load_pem_public_key(_read_pem(path_or_pem))  # type: ignore[return-value]


# ── Key generation helpers ───────────────────────────────────

def generate_keypair(
    private_key_path: str = "keys/private.pem",
    public_key_path: str = "keys/public.pem",
) -> None:
    """Generate and persist an RSA-4096 keypair (v0.2.x legacy)."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    with open(private_key_path, "wb") as f:
        f.write(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ))
    with open(public_key_path, "wb") as f:
        f.write(key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ))
    print(f"Keypair written: {private_key_path} / {public_key_path}")


def generate_ecdsa_keypair(
    private_key_path: str = "keys/ecdsa-private.pem",
    public_key_path: str = "keys/ecdsa-public.pem",
) -> None:
    """Generate and persist an ECDSA P-256 keypair (v0.3.0+)."""
    key = ec.generate_private_key(SECP256R1())
    with open(private_key_path, "wb") as f:
        f.write(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ))
    with open(public_key_path, "wb") as f:
        f.write(key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ))
    print(f"ECDSA P-256 keypair written: {private_key_path} / {public_key_path}")


# ── Signer ───────────────────────────────────────────────────

class CDSSigner:
    def __init__(self, private_key: str, issuer: str = "signed-data.org"):
        """
        Args:
            private_key: PEM file path OR PEM string (RSA or ECDSA P-256).
            issuer:      Organisation identifier attached to every signature.
        """
        self._key = _load_private(private_key)
        self.issuer = issuer
        self._is_ecdsa = isinstance(self._key, EllipticCurvePrivateKey)

    @property
    def key_id(self) -> str:
        return KEY_URI_ECDSA_V1 if self._is_ecdsa else KEY_URI_RSA_V0

    def _raw_sign(self, data: bytes) -> bytes:
        if isinstance(self._key, EllipticCurvePrivateKey):
            return self._key.sign(data, ECDSA(hashes.SHA256()))
        return self._key.sign(data, _PSS, hashes.SHA256())

    def sign(self, event: CDSEvent) -> CDSEvent:
        """Sign a CDSEvent, populating event.integrity."""
        canonical = event.canonical_bytes()
        raw_sig = self._raw_sign(canonical)
        event.integrity = IntegrityMeta(
            hash="sha256:" + hashlib.sha256(canonical).hexdigest(),
            signature=base64.b64encode(raw_sig).decode(),
            signed_by=self.issuer,
            key_id=self.key_id,
        )
        return event

    def sign_vc20(self, event: CDSEvent) -> dict[str, Any]:
        """Sign a CDSEvent and return a W3C VC 2.0 VerifiableCredential dict.

        Only valid for ECDSA keys — RSA is not supported in ecdsa-rdfc-2022.
        """
        if not self._is_ecdsa:
            raise ValueError("VC 2.0 signing requires an ECDSA P-256 key.")
        canonical = event.canonical_bytes_vc20()
        raw_sig = self._raw_sign(canonical)
        proof_value = "u" + base64.urlsafe_b64encode(raw_sig).rstrip(b"=").decode()
        vc = event.to_vc20()
        vc["proof"] = DataIntegrityProof(
            verification_method=VERIFICATION_METHOD_KEY1,
            created=event.ingested_at,
            proof_value=proof_value,
        ).to_dict()
        return vc


# ── Verifier ─────────────────────────────────────────────────

class CDSVerifier:
    def __init__(self, public_key: str):
        """Args: public_key: PEM file path OR PEM string (RSA or ECDSA P-256)."""
        self._key = _load_public(public_key)
        self._is_ecdsa = isinstance(self._key, EllipticCurvePublicKey)

    def verify(self, event: CDSEvent) -> bool:
        """Returns True or raises on any integrity failure."""
        if not event.integrity:
            raise ValueError("Event has no integrity metadata.")
        canonical = event.canonical_bytes()
        expected = "sha256:" + hashlib.sha256(canonical).hexdigest()
        if expected != event.integrity.hash:
            raise ValueError(f"Hash mismatch. Expected {expected}")

        if isinstance(self._key, EllipticCurvePublicKey):
            self._key.verify(
                base64.b64decode(event.integrity.signature),
                canonical,
                ECDSA(hashes.SHA256()),
            )
        else:
            self._key.verify(
                base64.b64decode(event.integrity.signature),
                canonical,
                _PSS,
                hashes.SHA256(),
            )
        return True

    def verify_vc20(self, vc: dict[str, Any]) -> bool:
        """Verify a W3C VC 2.0 VerifiableCredential. Returns True or raises."""
        proof = vc.get("proof")
        if not proof or proof.get("type") != "DataIntegrityProof":
            raise ValueError("Document has no DataIntegrityProof.")
        if not isinstance(self._key, EllipticCurvePublicKey):
            raise ValueError("VC 2.0 verification requires an ECDSA P-256 public key.")

        pv = proof["proofValue"]
        if not pv.startswith("u"):
            raise ValueError(f"Unsupported multibase prefix in proofValue: {pv[:1]!r}")
        raw_sig = base64.urlsafe_b64decode(pv[1:] + "==")

        event = CDSEvent.from_vc20(vc)
        canonical = event.canonical_bytes_vc20()
        try:
            self._key.verify(raw_sig, canonical, ECDSA(hashes.SHA256()))
        except InvalidSignature as exc:
            raise ValueError("VC 2.0 signature verification failed.") from exc
        return True
