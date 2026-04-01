"""
SignedData CDS — Signer & Verifier
RSA-PSS SHA-256.  Keys are PEM file paths or PEM strings.
"""
from __future__ import annotations

import base64
import hashlib

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from cds.schema import CDSEvent, IntegrityMeta


def generate_keypair(
    private_key_path: str = "keys/private.pem",
    public_key_path: str  = "keys/public.pem",
) -> None:
    """Generate and persist an RSA-4096 keypair."""
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
    print(f"✅ Keypair: {private_key_path} / {public_key_path}")


def _load_private(path_or_pem: str) -> RSAPrivateKey:
    data = (
        open(path_or_pem, "rb").read()
        if not path_or_pem.startswith("-----")
        else path_or_pem.encode()
    )
    return serialization.load_pem_private_key(data, password=None)  # type: ignore[return-value]


def _load_public(path_or_pem: str) -> RSAPublicKey:
    data = (
        open(path_or_pem, "rb").read()
        if not path_or_pem.startswith("-----")
        else path_or_pem.encode()
    )
    return serialization.load_pem_public_key(data)  # type: ignore[return-value]


_PSS = padding.PSS(
    mgf=padding.MGF1(hashes.SHA256()),
    salt_length=padding.PSS.MAX_LENGTH,
)


class CDSSigner:
    def __init__(self, private_key: str, issuer: str = "signed-data.org"):
        """
        Args:
            private_key: PEM file path OR PEM string.
            issuer:      Organisation identifier attached to every signature.
        """
        self._key: RSAPrivateKey = _load_private(private_key)
        self.issuer = issuer

    def sign(self, event: CDSEvent) -> CDSEvent:
        canonical = event.canonical_bytes()
        payload_hash = "sha256:" + hashlib.sha256(canonical).hexdigest()
        raw_sig = self._key.sign(canonical, _PSS, hashes.SHA256())
        event.integrity = IntegrityMeta(
            hash=payload_hash,
            signature=base64.b64encode(raw_sig).decode(),
            signed_by=self.issuer,
        )
        return event


class CDSVerifier:
    def __init__(self, public_key: str):
        """Args: public_key: PEM file path OR PEM string."""
        self._key: RSAPublicKey = _load_public(public_key)

    def verify(self, event: CDSEvent) -> bool:
        """Returns True or raises on any integrity failure."""
        if not event.integrity:
            raise ValueError("Event has no integrity metadata.")
        canonical = event.canonical_bytes()
        expected  = "sha256:" + hashlib.sha256(canonical).hexdigest()
        if expected != event.integrity.hash:
            raise ValueError(f"Hash mismatch. Expected {expected}")
        self._key.verify(
            base64.b64decode(event.integrity.signature),
            canonical, _PSS, hashes.SHA256(),
        )
        return True
