"""Tests for W3C VC 2.0 profile — to_vc20, from_vc20, sign_vc20, verify_vc20."""

from __future__ import annotations

import base64
from datetime import UTC, datetime

import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from cds.schema import CDSEvent, DataIntegrityProof, IntegrityMeta, SourceMeta
from cds.signer import CDSSigner, CDSVerifier, generate_ecdsa_keypair
from cds.vocab import (
    ISSUER_DID,
    VC20_CONTEXT,
    VC20_CRYPTOSUITE,
    CDSSources,
    CDSVocab,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_event(**overrides) -> CDSEvent:
    base = dict(
        content_type=CDSVocab.LOTTERY_MEGA_SENA,
        source=SourceMeta(**{"@id": CDSSources.CAIXA_LOTERIAS}),
        occurred_at=datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC),
        lang="pt-BR",
        payload={"concurso": 2800, "dezenas": ["05", "10", "20", "30", "40", "50"]},
    )
    base.update(overrides)
    return CDSEvent(**base)


@pytest.fixture()
def event():
    return _make_event()


@pytest.fixture()
def ecdsa_key_pem(tmp_path):
    priv = tmp_path / "priv.pem"
    pub = tmp_path / "pub.pem"
    generate_ecdsa_keypair(str(priv), str(pub))
    return str(priv), str(pub)


@pytest.fixture()
def signer(ecdsa_key_pem):
    return CDSSigner(ecdsa_key_pem[0])


@pytest.fixture()
def verifier(ecdsa_key_pem):
    return CDSVerifier(ecdsa_key_pem[1])


# ── to_vc20 ───────────────────────────────────────────────────────────────────


def test_to_vc20_context(event):
    vc = event.to_vc20()
    assert vc["@context"][0] == VC20_CONTEXT
    assert "signed-data.org/contexts/cds/v1.jsonld" in vc["@context"][1]


def test_to_vc20_type(event):
    vc = event.to_vc20()
    assert "VerifiableCredential" in vc["type"]
    assert "CDSEvent" in vc["type"]


def test_to_vc20_issuer(event):
    vc = event.to_vc20()
    assert vc["issuer"] == ISSUER_DID


def test_to_vc20_id_is_event_uri(event):
    vc = event.to_vc20()
    assert vc["id"].startswith("https://signed-data.org/events/")
    assert event.id in vc["id"]


def test_to_vc20_credential_subject(event):
    vc = event.to_vc20()
    subj = vc["credentialSubject"]
    assert subj["content_type"] == CDSVocab.LOTTERY_MEGA_SENA
    assert subj["source"]["@id"] == CDSSources.CAIXA_LOTERIAS
    assert subj["lang"] == "pt-BR"
    assert subj["payload"]["concurso"] == 2800


def test_to_vc20_credential_subject_id_has_fragment(event):
    vc = event.to_vc20()
    assert vc["credentialSubject"]["@id"].endswith("#subject")


def test_to_vc20_no_proof_without_integrity(event):
    vc = event.to_vc20()
    assert "proof" not in vc


def test_to_vc20_proof_from_integrity(event):
    sig_bytes = b"\x01\x02\x03" * 20
    event.integrity = IntegrityMeta(
        hash="sha256:abc",
        signature=base64.b64encode(sig_bytes).decode(),
        signed_by="https://signed-data.org",
        key_id="did:web:signed-data.org#key-1",
    )
    vc = event.to_vc20()
    proof = vc["proof"]
    assert proof["type"] == "DataIntegrityProof"
    assert proof["cryptosuite"] == VC20_CRYPTOSUITE
    assert proof["proofPurpose"] == "assertionMethod"
    assert proof["verificationMethod"] == "did:web:signed-data.org#key-1"
    # proofValue must start with multibase base64url prefix
    assert proof["proofValue"].startswith("u")
    # round-trip the signature bytes
    recovered = base64.urlsafe_b64decode(proof["proofValue"][1:] + "==")
    assert recovered == sig_bytes


# ── from_vc20 ─────────────────────────────────────────────────────────────────


def test_from_vc20_round_trip(event):
    vc = event.to_vc20()
    restored = CDSEvent.from_vc20(vc)
    assert restored.content_type == event.content_type
    assert restored.source.id == event.source.id
    assert restored.lang == event.lang
    assert restored.payload == event.payload


def test_from_vc20_reconstructs_uuid(event):
    vc = event.to_vc20()
    restored = CDSEvent.from_vc20(vc)
    assert restored.id == event.id


def test_from_vc20_with_proof(event):
    sig_bytes = b"\xde\xad\xbe\xef" * 16
    event.integrity = IntegrityMeta(
        hash="sha256:abc",
        signature=base64.b64encode(sig_bytes).decode(),
        signed_by="https://signed-data.org",
        key_id="did:web:signed-data.org#key-1",
    )
    vc = event.to_vc20()
    restored = CDSEvent.from_vc20(vc)
    assert restored.integrity is not None
    recovered_sig = base64.b64decode(restored.integrity.signature)
    assert recovered_sig == sig_bytes


# ── DataIntegrityProof model ──────────────────────────────────────────────────


def test_data_integrity_proof_serialisation():
    proof = DataIntegrityProof(
        verificationMethod="did:web:signed-data.org#key-1",
        created=datetime(2026, 1, 15, tzinfo=UTC),
        proofValue="uABCD",
    )
    d = proof.to_dict()
    assert d["type"] == "DataIntegrityProof"
    assert d["cryptosuite"] == VC20_CRYPTOSUITE
    assert d["proofPurpose"] == "assertionMethod"
    assert d["verificationMethod"] == "did:web:signed-data.org#key-1"
    assert d["proofValue"] == "uABCD"


# ── sign_vc20 / verify_vc20 ───────────────────────────────────────────────────


def test_sign_vc20_produces_valid_structure(event, signer):
    vc = signer.sign_vc20(event)
    assert vc["type"] == ["VerifiableCredential", "CDSEvent"]
    assert vc["issuer"] == ISSUER_DID
    proof = vc["proof"]
    assert proof["type"] == "DataIntegrityProof"
    assert proof["cryptosuite"] == VC20_CRYPTOSUITE
    assert proof["proofValue"].startswith("u")


def test_sign_vc20_verify_vc20_round_trip(event, signer, verifier):
    vc = signer.sign_vc20(event)
    assert verifier.verify_vc20(vc) is True


def test_verify_vc20_rejects_tampered_payload(event, signer, verifier):
    vc = signer.sign_vc20(event)
    vc["credentialSubject"]["payload"]["concurso"] = 9999
    with pytest.raises(Exception):
        verifier.verify_vc20(vc)


def test_verify_vc20_rejects_missing_proof(event, verifier):
    vc = event.to_vc20()
    with pytest.raises(ValueError, match="DataIntegrityProof"):
        verifier.verify_vc20(vc)


def test_sign_vc20_raises_for_rsa_key(tmp_path, event):
    from cds.signer import generate_keypair

    priv = tmp_path / "rsa-priv.pem"
    pub = tmp_path / "rsa-pub.pem"
    generate_keypair(str(priv), str(pub))
    rsa_signer = CDSSigner(str(priv))
    with pytest.raises(ValueError, match="ECDSA"):
        rsa_signer.sign_vc20(event)


def test_sign_vc20_canonical_bytes_are_stable(event, signer):
    # canonical_bytes_vc20 must return identical bytes across calls
    b1 = event.canonical_bytes_vc20()
    b2 = event.canonical_bytes_vc20()
    assert b1 == b2
