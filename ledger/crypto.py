"""Ed25519 signing and SHA-256 helpers used by the evidence ledger."""

import hashlib
import os
from typing import Tuple

import nacl.exceptions
import nacl.signing
from dotenv import load_dotenv


def generate_keypair() -> dict[str, str]:
    signing_key = nacl.signing.SigningKey.generate()
    return {
        "private_key": signing_key.encode().hex(),
        "public_key": signing_key.verify_key.encode().hex(),
    }


def sign_message(private_key_hex: str, message: bytes) -> str:
    return nacl.signing.SigningKey(bytes.fromhex(private_key_hex)).sign(message).signature.hex()


def verify_signature(public_key_hex: str, message: bytes, signature_hex: str | None) -> bool:
    if not signature_hex:
        return False
    try:
        nacl.signing.VerifyKey(bytes.fromhex(public_key_hex)).verify(
            message, bytes.fromhex(signature_hex)
        )
    except (ValueError, TypeError, nacl.exceptions.BadSignatureError):
        return False
    return True


def sha256_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_keys_from_env() -> Tuple[str | None, str | None]:
    load_dotenv()
    return os.getenv("PRIVATE_KEY_HEX"), os.getenv("PUBLIC_KEY_HEX")
