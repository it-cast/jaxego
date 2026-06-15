"""Gera os secrets/chaves de produção e escreve apps/api/.env (gitignored).

Roda NO SERVIDOR (os segredos nascem lá, nunca trafegam pelo chat):

    cd apps/api
    uv run python -m tools.gen_secrets          # cria .env se não existir
    uv run python -m tools.gen_secrets --print  # só imprime as linhas (não escreve)

Formatos (validados contra o código):
- JWT_SECRET                : token_urlsafe (>=256 bits) — auth HS256 (essencial)
- SAFE2PAY_TOKEN_ENCRYPT_KEY: 64 hex (AES-256-GCM do token do cartão)
- SAFE2PAY_WEBHOOK_SECRET   : token_urlsafe (HMAC do webhook)
- RSA_PRIVATE_KEY/PUBLIC    : base64(PEM) single-line (crypto.py aceita PEM ou base64(PEM))
- VAPID_PRIVATE_KEY         : base64url do escalar privado (32 bytes) — pywebpush from_string
- VAPID_PUBLIC_KEY          : base64url do ponto público não-comprimido (65 bytes) — applicationServerKey

Os valores `__PREENCHER__` são de CONTA EXTERNA (você fornece): DATABASE_URL, B2, SES, SMS.
Safe2Pay fica em sandbox/desligado no piloto direto (DEC-004); ligar com o contrato.
"""

from __future__ import annotations

import base64
import secrets
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _gen() -> dict[str, str]:
    # RSA-2048 (cartão — usado só quando cartão/PIX ligar; gerado já pronto).
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    pub_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    # VAPID EC P-256 (web push — best-effort no piloto).
    vapid = ec.generate_private_key(ec.SECP256R1())
    d = vapid.private_numbers().private_value.to_bytes(32, "big")
    point = vapid.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    return {
        "JWT_SECRET": secrets.token_urlsafe(48),
        "SAFE2PAY_TOKEN_ENCRYPT_KEY": secrets.token_hex(32),
        "SAFE2PAY_WEBHOOK_SECRET": secrets.token_urlsafe(36),
        "RSA_PRIVATE_KEY": base64.b64encode(priv_pem).decode(),
        "RSA_PUBLIC_KEY": base64.b64encode(pub_pem).decode(),
        "VAPID_PRIVATE_KEY": _b64url(d),
        "VAPID_PUBLIC_KEY": _b64url(point),
    }


def _env_body(s: dict[str, str]) -> str:
    return f"""# ──────────────────────────────────────────────────────────────────────────
# Jaxegô — .env de PRODUÇÃO (piloto direto). NUNCA commitar (gitignored).
# Gerado por tools.gen_secrets. Valores __PREENCHER__ são de conta externa.
# ──────────────────────────────────────────────────────────────────────────
ENVIRONMENT=production
APP_VERSION=1.0.0
LOG_LEVEL=INFO

# --- Infra (você fornece) ---
DATABASE_URL=__PREENCHER__   # mysql+aiomysql://USER:SENHA@HOST:3306/jaxego?charset=utf8mb4
REDIS_URL=redis://localhost:6379/0
SENTRY_DSN=                  # opcional, mas recomendado (observabilidade)

# --- Auth (gerado — ESSENCIAL) ---
JWT_SECRET={s["JWT_SECRET"]}

# --- Receita Federal (CNPJ) — defaults públicos OK ---
RECEITA_BASE_URL=https://minhareceita.org
RECEITA_BRASILAPI_URL=https://brasilapi.com.br/api/cnpj/v1
RECEITA_ALLOWLIST_HOSTS=minhareceita.org,brasilapi.com.br

# --- Backblaze B2 (docs KYC + comprovação) — OBRIGATÓRIO no piloto ---
B2_KEY_ID=__PREENCHER__
B2_APP_KEY=__PREENCHER__
B2_ENDPOINT_URL=https://s3.us-west-004.backblazeb2.com
B2_REGION=us-west-004
B2_KYC_BUCKET=__PREENCHER__
B2_ALLOWLIST_HOSTS=s3.us-west-004.backblazeb2.com

# --- E-mail SES (notificações) — OBRIGATÓRIO ---
SES_SEND_URL=https://email.sa-east-1.amazonaws.com/send
SES_API_TOKEN=__PREENCHER__
SES_ALLOWLIST_HOSTS=email.sa-east-1.amazonaws.com

# --- SMS Zenvia ("a caminho") — opcional (degrada p/ e-mail+push) ---
SMS_ZENVIA_URL=https://api.zenvia.com/v2/channels/sms/messages
SMS_ZENVIA_TOKEN=__PREENCHER__
SMS_ALLOWLIST_HOSTS=api.zenvia.com

# --- Geocoding / OSRM — públicos OK (ver TD-014/TD-019 p/ volume) ---
GEOCODING_BASE_URL=https://nominatim.openstreetmap.org
GEOCODING_ALLOWLIST_HOSTS=nominatim.openstreetmap.org
OSRM_BASE_URL=https://router.project-osrm.org
OSRM_PROFILE=driving
OSRM_ALLOWLIST_HOSTS=router.project-osrm.org

# --- Web Push VAPID (best-effort; degrada p/ e-mail/polling) ---
VAPID_PRIVATE_KEY={s["VAPID_PRIVATE_KEY"]}
VAPID_PUBLIC_KEY={s["VAPID_PUBLIC_KEY"]}
VAPID_CLAIM_SUB=mailto:ops@jaxego.com.br

# --- Safe2Pay — DESLIGADO no piloto direto (liga com o contrato — DEC-004/TD-10-0x) ---
SAFE2PAY_SANDBOX=true
SAFE2PAY_API_KEY=
SAFE2PAY_TOKEN_ENCRYPT_KEY={s["SAFE2PAY_TOKEN_ENCRYPT_KEY"]}
SAFE2PAY_WEBHOOK_SECRET={s["SAFE2PAY_WEBHOOK_SECRET"]}
RSA_PRIVATE_KEY={s["RSA_PRIVATE_KEY"]}
RSA_PUBLIC_KEY={s["RSA_PUBLIC_KEY"]}
SAFE2PAY_JAXEGO_RECIPIENT=
REVENUE_SHARE_DEFAULT_PCT=10

# --- LLM — desligado no M1 (infra-only) ---
LLM_PROVIDER=stub
"""


def main() -> None:
    do_print = "--print" in sys.argv
    secs = _gen()

    if do_print:
        for k, v in secs.items():
            print(f"{k}={v}")
        return

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        print(f"[!] {env_path} ja existe -- NAO sobrescrevi.")
        print("    Rode com --print para ver os secrets e cole manualmente, ou apague o .env primeiro.")
        return

    env_path.write_text(_env_body(secs), encoding="utf-8")
    print(f"[OK] Escrito {env_path}")
    print("     Proximo: preencha os valores __PREENCHER__ (DATABASE_URL, B2_*, SES_*, SMS opcional).")
    print("     Conferir: nenhum __PREENCHER__ deve sobrar antes de subir a API.")


if __name__ == "__main__":
    main()
