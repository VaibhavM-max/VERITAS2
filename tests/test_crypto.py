from ledger.crypto import generate_keypair, sha256_hash, sign_message, verify_signature


def test_sign_and_verify() -> None:
    keys = generate_keypair()
    message = b"VERITAS evidence"
    signature = sign_message(keys["private_key"], message)
    assert verify_signature(keys["public_key"], message, signature)
    assert not verify_signature(keys["public_key"], b"tampered", signature)


def test_hash_is_deterministic() -> None:
    assert sha256_hash(b"data") == sha256_hash(b"data")
    assert len(sha256_hash(b"data")) == 64
