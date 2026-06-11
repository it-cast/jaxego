"""Crypto round-trip: AES-256-GCM (token) + RSA-OAEP-2048 (card) — D-02 / TH-A/TH-B.

The Python `cryptography` AES-GCM layout is `base64(nonce[12] + ct_with_tag)` —
NOT the Node `iv+tag+ct` layout (Pitfall 1). A tampered token raises (never returns
the blob — the Node plaintext-legacy fallback is deliberately NOT ported).
"""

from __future__ import annotations

import base64
import json

import pytest


def test_token_round_trip(crypto_keys) -> None:
    from app.payments.crypto import decrypt_token, encrypt_token

    blob = encrypt_token("tok_abc123")
    assert blob != "tok_abc123"  # not plaintext
    assert decrypt_token(blob) == "tok_abc123"


def test_token_layout_is_nonce_plus_ct_with_tag(crypto_keys) -> None:
    from app.payments.crypto import encrypt_token

    blob = encrypt_token("x")
    raw = base64.b64decode(blob)
    # nonce(12) + ciphertext(1 byte of plaintext) + tag(16) = 29 bytes minimum.
    assert len(raw) == 12 + 1 + 16


def test_token_tampered_raises_not_returns_blob(crypto_keys) -> None:
    from app.payments.crypto import decrypt_token, encrypt_token

    blob = encrypt_token("tok_secret")
    raw = bytearray(base64.b64decode(blob))
    raw[-1] ^= 0xFF  # flip the last byte of the auth tag
    tampered = base64.b64encode(bytes(raw)).decode()
    with pytest.raises(RuntimeError):
        decrypt_token(tampered)


def test_token_key_rejects_bad_length(monkeypatch) -> None:
    from app.core import config as config_mod

    monkeypatch.setenv("SAFE2PAY_TOKEN_ENCRYPT_KEY", "deadbeef")  # 8 hex, not 64
    config_mod.get_settings.cache_clear()
    config_mod.settings = config_mod.get_settings()
    import app.payments.crypto as crypto_mod

    crypto_mod.settings = config_mod.settings
    with pytest.raises(RuntimeError):
        crypto_mod.encrypt_token("x")
    config_mod.get_settings.cache_clear()
    config_mod.settings = config_mod.get_settings()


def test_rsa_decrypt_card(crypto_keys) -> None:
    from app.payments.crypto import rsa_decrypt_card

    from tests.payments.conftest import rsa_encrypt_for_backend

    _private_pem, public_pem = crypto_keys
    card = {
        "nomeTitular": "JOAO DA SILVA",
        "numeroCartao": "4111111111111111",
        "validade": "12/2027",
        "cvv": "123",
    }
    blob = rsa_encrypt_for_backend(public_pem, json.dumps(card))
    plain = rsa_decrypt_card(blob)
    assert json.loads(plain)["numeroCartao"] == "4111111111111111"


def test_rsa_decrypt_garbage_raises(crypto_keys) -> None:
    from app.payments.crypto import rsa_decrypt_card

    with pytest.raises(Exception):  # noqa: B017 — any decrypt failure must raise, never leak
        rsa_decrypt_card(base64.b64encode(b"not-a-valid-ciphertext").decode())
