"""Card/token crypto: AES-256-GCM (token at rest) + RSA-OAEP-2048 (card in transit).

D-02 / TH-A / TH-B. Two primitives, both from the PyCA `cryptography` lib (already a
dependency — no new install):

- `encrypt_token` / `decrypt_token` — AES-256-GCM of the Safe2Pay card token at rest.
  **⚠ Python layout (Pitfall 1):** `AESGCM.encrypt()` ALREADY appends the 16-byte tag
  to the END of the ciphertext, so the stored format is `base64(nonce[12] + ct_with_tag)`
  — NOT the Node `iv+tag+ct` layout from SAAS-BILLING §4.1. A tampered token raises
  `RuntimeError` (InvalidTag); we deliberately do NOT port the Node plaintext-legacy
  fallback (`return encryptedBase64`) — that would leak/accept garbage.

- `rsa_decrypt_card` — the backend decrypts the `{nomeTitular,numeroCartao,validade,cvv}`
  JSON the frontend encrypted with the RSA public key (OAEP/SHA-256). The private key
  lives ONLY in env (`RSA_PRIVATE_KEY`); the public key is served via GET to the client.
  The plaintext card NEVER persists, NEVER logs (A09).

Keys are read from `settings` (env only — Gate 8 FAIL-BLOCK if a real value is committed).
"""

from __future__ import annotations

import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings

_NONCE_BYTES = 12


def _token_key() -> bytes:
    """The 32-byte AES key from `SAFE2PAY_TOKEN_ENCRYPT_KEY` (64 hex chars)."""
    hexkey = settings.safe2pay_token_encrypt_key
    if not hexkey or len(hexkey) != 64:
        raise RuntimeError("SAFE2PAY_TOKEN_ENCRYPT_KEY inválida: 64 chars hex (32 bytes).")
    try:
        return bytes.fromhex(hexkey)
    except ValueError as exc:
        raise RuntimeError("SAFE2PAY_TOKEN_ENCRYPT_KEY não é hex válido.") from exc


def encrypt_token(plain: str) -> str:
    """AES-256-GCM encrypt → base64(nonce[12] + ciphertext_with_tag).

    The lib's `encrypt()` output already includes the 16-byte tag at the end; we
    only prepend the 12-byte nonce. NEVER replicate the Node iv+tag+ct split.
    """
    aesgcm = AESGCM(_token_key())
    nonce = os.urandom(_NONCE_BYTES)
    ct = aesgcm.encrypt(nonce, plain.encode(), None)  # ct = real_ct || tag(16)
    return base64.b64encode(nonce + ct).decode()


def decrypt_token(blob: str) -> str:
    """Decrypt a `base64(nonce[12] + ct_with_tag)` token.

    A tampered/forged token raises `RuntimeError` (InvalidTag) — we NEVER return the
    blob (the Node plaintext-legacy fallback is a security bug, not ported).
    """
    try:
        raw = base64.b64decode(blob)
    except (ValueError, TypeError) as exc:
        raise RuntimeError("token de cartão inválido (base64).") from exc
    if len(raw) <= _NONCE_BYTES + 16:
        raise RuntimeError("token de cartão truncado.")
    nonce, ct = raw[:_NONCE_BYTES], raw[_NONCE_BYTES:]
    try:
        return AESGCM(_token_key()).decrypt(nonce, ct, None).decode()
    except InvalidTag as exc:
        raise RuntimeError("token de cartão corrompido/adulterado.") from exc


def _load_private_key() -> RSAPrivateKey:
    """Load the RSA private key from env (PEM or base64(PEM))."""
    pem = settings.rsa_private_key
    if not pem:
        raise RuntimeError("RSA_PRIVATE_KEY ausente.")
    if not pem.lstrip().startswith("-----"):
        pem = base64.b64decode(pem).decode()
    key = serialization.load_pem_private_key(pem.encode(), password=None)
    if not isinstance(key, RSAPrivateKey):
        raise RuntimeError("RSA_PRIVATE_KEY não é uma chave RSA.")
    return key


def rsa_decrypt_card(b64_ciphertext: str) -> str:
    """Decrypt the RSA-OAEP(SHA-256) card blob from the frontend → JSON string.

    Any decrypt failure raises — the function NEVER returns the raw ciphertext.
    The returned plaintext (card JSON) MUST NOT be logged or persisted (A09).
    """
    key = _load_private_key()
    ciphertext = base64.b64decode(b64_ciphertext)
    plain = key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return plain.decode()


def public_key_pem() -> str:
    """The RSA public key as a PEM string, served to the client via GET."""
    pem = settings.rsa_public_key
    if not pem:
        raise RuntimeError("RSA_PUBLIC_KEY ausente.")
    if not pem.lstrip().startswith("-----"):
        pem = base64.b64decode(pem).decode()
    return pem
