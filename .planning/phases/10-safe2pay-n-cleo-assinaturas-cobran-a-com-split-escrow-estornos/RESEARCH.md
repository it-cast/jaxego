# Phase 10: Safe2Pay núcleo — assinaturas, cobrança com split, escrow, estornos - Research

**Researched:** 2026-06-11
**Domain:** Pagamento online (PSP Safe2Pay) — assinatura recorrente, cobrança split por entrega, escrow interno, estornos, webhooks
**Confidence:** HIGH na mecânica de criptografia/assinatura recorrente (SAAS-BILLING é lei + verificada na lib `cryptography`); MEDIUM na arquitetura de escrow/ledger (padrão claro, schema é discrição); LOW no contrato exato de split/subconta da API Safe2Pay (DEC-003 — `[ASSUMIDO]`)
**⚠ É DINHEIRO REAL. Gate 4 (Security Baseline) obrigatório e exaustivo abaixo.**

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (copiadas verbatim do 10-CONTEXT.md)

- **D-01 (DEC-003 — REVISAR com contrato Safe2Pay):** `[ASSUMIDO]` split/marketplace DISPONÍVEL no plano contratado. `[ASSUMIDO]` escrow interno 24h pós-FINALIZADA MANTIDO independente do prazo de repasse do PSP. `[ASSUMIDO]` taxa por transação parametrizável (seed/config, nunca hardcoded). Tudo atrás de interface própria.
- **D-02 — Criptografia (não muda):** token de cartão Safe2Pay em **AES-256-GCM** (`base64(iv12+tag16+ciphertext)`, chave `SAFE2PAY_TOKEN_ENCRYPT_KEY` 32 bytes hex); dados de cartão do frontend em **RSA-OAEP 2048** (frontend cifra com chave pública, backend decifra com privada — cartão NUNCA em texto puro nem em log). Endpoint GET de chave pública RSA. (SAAS-BILLING §4/§13).
- **D-03 — Assinatura recorrente da loja:** cartão tokenizado (sandbox cobra raw; produção tokeniza→cobra com token) + PIX automático (autorização v3 + agendamento + webhooks). Estados: trial/active/blocked/cancelado. Cron diário. Inadimplência: >10d → blocked, >20d → cancelado. Guard de assinatura ativa. (SAAS-BILLING §5-10).
- **D-04 — Webhooks Safe2Pay** (sem auth nativa, idempotentes por IdTransaction, logar payload em webhook_logs antes de processar, responder 200 <5s, trabalho pesado em fila arq). Validar assinatura/token do header. (SAAS-BILLING §8, integracoes.md §1).
- **D-05 — Cobrança por entrega cartão/PIX na CRIAÇÃO** (F-03): `Amount = corrida + taxa`; **Split**: subconta_entregador ← corrida; conta_jaxego ← taxa (+ revenue share da área, default 20% `[ASSUMIDO]` OQ-1). Recusa na criação → entrega NÃO nasce (F-03 E3). (integracoes.md §1, ADR-009 v2).
- **D-06 — Escrow interno 24h:** corrida retida em escrow após cobrança; FINALIZADA (Phase 9) + 24h sem disputa → libera no saldo sacável do entregador (saque é Phase 11). Tabela `platform_charges` com idempotency key + IdTransaction. (RN-006, F-07, entidades platform_charges).
- **D-07 — Subconta do entregador:** cadastrada como recebedor/subconta Safe2Pay quando o MEI é aprovado no KYC (Phase 5 — gancho `mei_pending`/MEI ativo). Sem MEI → sem subconta → sem repasse via plataforma (RN-010; direto da Phase 7-9 continua). (integracoes.md §1, RN-010).
- **D-08 — Estornos:** cancelamento pré-aceite → estorno total automático; parcial conforme RN-004 (50%/100%+retorno) com estorno do excedente em até 5 dias úteis. Conciliação diária contra extrato Safe2Pay (diferença >R$0,01 → alerta admin plataforma). (integracoes.md §1, RN-004, F-07 E1).
- **D-09 — Interface própria (ADR-009 v2):** Safe2Pay atrás de Protocol/adapter (`PaymentPort`) + impl httpx + **Stub de dev/teste** (NUNCA chamar API real nos testes; sandbox documentado). Trocar de PSP ou ajustar escrow = trocar impl, não o domínio.

### Claude's Discretion
- Lib de cripto Python (`cryptography` — AES-GCM + RSA-OAEP; já presente desde Phase 1).
- Estrutura de `platform_charges`/`merchant_subscriptions` (estende Phase 4) e escrow ledger.
- Mecânica do cron de cobrança (arq) e conciliação.

### Deferred Ideas (OUT OF SCOPE — Phase 11/13)
- Fatura mensal de taxas do pagamento direto + bloqueio por fatura vencida (RN-025) — Phase 11.
- Disputas (mediação) + saques (payouts) — Phase 11.
- Relatório de revenue share do admin de área — Phase 13.
- Confirmação do contrato Safe2Pay (split/prazo/taxa reais) → ADR que supera DEC-003.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Descrição | Research Support |
|----|-----------|------------------|
| REQ-010 | Assinatura recorrente via Safe2Pay (cartão/PIX, status, idempotência, webhook recorrente) | §"Assinatura recorrente" + SAAS-BILLING §5-10; webhook idempotente por IdTransaction (Security Baseline TH-D, TH-E) |
| REQ-011 | Limite de plano + upgrade pro-rata/downgrade agendado (RN-028/029) | §"Assinatura recorrente — upgrade/downgrade"; cálculo pro-rata em centavos (TH-F integridade) |
| REQ-019 | Regras de MEI (RN-010 + RN-024) — subconta só com MEI ativo | §"Subconta do entregador (D-07)"; gancho Phase 5 `mei_pending`/MEI ativo |
| REQ-034 | Cobrança por entrega cartão/PIX com split Safe2Pay (PaymentPort, idempotência por Reference, recusa→não nasce, circuit breaker) | §"Cobrança split por entrega" + §"PaymentPort"; Security Baseline TH-D/TH-F |
| REQ-036 | Escrow interno 24h (RN-006) — job FINALIZADA+24h sem disputa | §"Escrow interno (D-06)" + ledger; reusa cron `finalize_deliveries` Phase 9 (Security Baseline TH-G) |
| REQ-029 | Cancelamento com matriz de custos / estornos (RN-004) | §"Estornos (D-08)"; Security Baseline TH-H (IDOR de estorno) |
</phase_requirements>

## Summary

Esta phase entrega o núcleo de pagamento online do Jaxegô via Safe2Pay, atrás de uma **interface própria** (`PaymentPort`, ADR-009 v2 / D-09) com impl httpx e **Stub** — exatamente o padrão já consolidado em `app/integrations/` (Protocol + httpx adapter + Stub, factory Stub em dev/test). A mecânica canônica de billing (`docs/SAAS-BILLING-DOCS.md`, referência NestJS) é **lei do projeto** (CLAUDE.md §18): criptografia AES-256-GCM do token de cartão, RSA-OAEP-2048 dos dados de cartão do frontend, assinatura recorrente cartão/PIX, cron diário, inadimplência 10/20 dias, webhooks idempotentes. A mecânica **não muda** ao portar de NestJS para FastAPI/SQLAlchemy/Python; só a implementação muda (lib `cryptography` em vez de `node:crypto`).

A skill `domain/safe2pay-escrow-br` (obrigatória, 546 linhas) cobre o que a SAAS-BILLING genérica NÃO cobre: o padrão `HasError` (resposta HTTP 200 NÃO significa sucesso), os 3 subdomínios Safe2Pay (`payment` cria / `api` administra / `services` consulta), estados de transação com escrow (PENDING→HELD→RELEASED/REFUNDED/FAILED), webhook idempotente por `(transaction_id, status)`, validação HMAC-SHA256 com `secrets.compare_digest`, e estorno com rotas distintas por método (Pix vs Cartão). O escrow interno de 24h é uma **camada de domínio Jaxegô independente do PSP** (RN-006): a corrida fica retida num ledger e só entra no saldo sacável 24h após FINALIZADA (Phase 9) sem disputa — reusa o cron `finalize_deliveries` já existente.

**Tudo nasce `[ASSUMIDO]` (DEC-003):** o contrato Safe2Pay (split/marketplace disponível? prazo de repasse? taxa por transação? formato exato de subconta/split na API?) não está confirmado. O split é implementado mas **parametrizado** (seed/config, nunca hardcoded — DRV-009), e o escrow de 24h é mantido independente do que o PSP fizer. A interface própria garante que trocar de PSP ou ajustar o escrow seja trocar a impl, não o domínio.

**Primary recommendation:** `PaymentPort` (Protocol) + `Safe2PayHttpAdapter` (httpx, com helper `_call_safe2pay` que SEMPRE checa `HasError`) + `PaymentStubAdapter` (dev/test, nunca rede), seguindo o padrão `app/integrations/base.py`/`factory.py`/`http.py`. Cripto com `cryptography` (`AESGCM` + `padding.OAEP`). Money em **centavos inteiros**. Idempotência em TODA escrita de cobrança. Webhook: logar → validar assinatura → deduplicar → enfileirar → responder 200. Escrow como ledger de domínio. Tudo parametrizado por seed/config.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Descriptografar dados de cartão (RSA-OAEP) | API / Backend | — | Chave privada SÓ no backend; cartão nunca trafega em texto puro (D-02, PCI-adjacent) |
| Cifrar dados de cartão (RSA-OAEP) | Frontend / Client | — | Frontend cifra com chave pública obtida via GET; backend nunca recebe texto puro |
| Tokenizar cartão + cobrar (Safe2Pay) | API / Backend (PaymentPort) | Safe2Pay (externo) | Lógica de PSP atrás de interface própria (D-09); só o adapter fala com Safe2Pay |
| Armazenar token AES-256-GCM | Database / Storage | API (cifra/decifra) | Token em repouso cifrado; decifrar só no cron de cobrança (D-02) |
| Cron diário de cobrança + inadimplência | API / Worker (arq) | Database | Reusa `WorkerSettings` cron_jobs (Phase 9); aware-UTC (TD-010) |
| Split corrida/taxa/revenue-share | API / Backend | Safe2Pay (externo) | Backend monta o split em centavos; NUNCA o frontend (TH-F) |
| Escrow interno 24h (ledger) | API / Backend + Worker | Database | Domínio Jaxegô (RN-006), independente do PSP; cron `finalize_deliveries`+24h |
| Webhooks Safe2Pay | API / Backend | Worker (arq) + Database | Endpoint público valida HMAC e deduplica; trabalho pesado em fila (D-04) |
| Subconta do entregador | API / Backend (PaymentPort) | Couriers/KYC (Phase 5) | Cadastro disparado por MEI aprovado (gancho `mei_pending`, D-07) |
| Estornos | API / Backend (PaymentPort) | Safe2Pay (externo) | Rotas distintas Pix/Cartão; ownership obrigatório (TH-H) |
| Conciliação diária | API / Worker (arq) | Database | Compara extrato Safe2Pay × `platform_charges`; alerta >R$0,01 (D-08) |

## Standard Stack

### Core (tudo já presente — nada novo a instalar)

| Library | Version (verificada) | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `cryptography` | `>=43,<46` (já em pyproject `apps/api`) `[VERIFIED: apps/api/pyproject.toml:14]` | AES-256-GCM (token cartão) + RSA-OAEP-2048 (dados cartão) | Lib oficial PyCA; `AESGCM` e `padding.OAEP` são as primitivas recomendadas `[CITED: github.com/pyca/cryptography aead.rst, rsa.rst]` |
| `httpx` | `>=0.28.1` (já em deps) `[VERIFIED: apps/api/pyproject.toml:25]` | Cliente async para Safe2Pay (impl do PaymentPort) | Já usado por todos os adapters; `build_client()` com redirects off + SSRF guard `[VERIFIED: app/integrations/http.py]` |
| `arq` | `>=0.26,<0.27` (já em deps) `[VERIFIED: apps/api/pyproject.toml:16]` | Cron diário de cobrança/inadimplência/escrow/conciliação | `WorkerSettings.cron_jobs` já existe (Phase 9 `finalize_deliveries`) `[VERIFIED: app/workers/settings.py]` |
| `SQLAlchemy` 2.x | (ADR-002) | Models `platform_charges`, escrow ledger, webhook_events, subscription state | Padrão do projeto; `UTC_DATETIME`/`BIG_ID`/`AreaScopedMixin` mixins `[VERIFIED: app/db/mixins.py]` |
| `pydantic` v2 | `>=2.7,<3` | Schemas de entrada (cartão cifrado, checkout) com tipos estreitos + `extra="forbid"` | A03 owasp; já padrão do projeto `[CITED: owasp A03]` |

**Instalação:** nenhuma — todas as libs já estão em `apps/api/pyproject.toml`.

**Version verification (npm não aplica — projeto Python):**
```bash
# já fixadas no pyproject; confirmar resolução no lockfile:
cd apps/api && uv lock --check    # cryptography 43-45, httpx 0.28+, arq 0.26
```
`cryptography` 43–45 estável; `AESGCM`/`OAEP` API estável há anos (mudança recente foi só `encrypt_into` zero-copy em 47.0.0, fora do nosso range). `[VERIFIED: ctx7 /pyca/cryptography]`

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `structlog` | (já em uso) | Logging estruturado com redação de campos sensíveis | TODO log de pagamento; NUNCA cartão/token/api-key (A09) `[VERIFIED: app/integrations/receita.py]` |
| `secrets` (stdlib) | — | `compare_digest` na validação HMAC do webhook | Anti timing-attack na assinatura (A02/A08) `[CITED: owasp anti-patterns]` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `cryptography` `AESGCM` | `PyNaCl` / `pycryptodome` | Desnecessário: `cryptography` já é dep (MySQL handshake) e oferece AES-GCM + RSA-OAEP. Não adicionar dep. |
| Escrow interno (ledger Jaxegô) | Confiar no escrow nativo do PSP | DEC-003: contrato não confirma prazo de repasse; RN-006 exige 24h pós-FINALIZADA controlado pelo domínio. Manter ledger interno. |
| `node:crypto` format `base64(iv12+tag16+ct)` | Format nativo do `cryptography` `base64(nonce12+ct_com_tag)` | **DIFERENÇA CRÍTICA, ver Pitfall 1:** no `cryptography`, `aesgcm.encrypt()` JÁ retorna ciphertext com a tag de 16 bytes anexada ao FINAL. Padronizar `base64(nonce[12] + ciphertext_que_inclui_tag)`. Não tentar replicar o layout iv+tag+ct do Node literalmente. |

## Architecture Patterns

### System Architecture Diagram

```
                         FRONTEND (Ionic/Angular — Phase 3/9)
                          │                          │
        GET chave pública │           checkout/cobrança (RSA-OAEP do cartão)
                          ▼                          ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  API FastAPI  (app/payments/  — NOVO módulo)                               │
│                                                                            │
│   router.py ──► service.py ──► PaymentPort (Protocol, base.py)             │
│      │              │              │                                        │
│      │              │              ├─► Safe2PayHttpAdapter (httpx + _call_safe2pay)
│      │              │              │       │  assert_safe_url (SSRF, A10)   │
│      │              │              │       ▼                                │
│      │              │              │   Safe2Pay  (payment / api / services) │
│      │              │              └─► PaymentStubAdapter (dev/test, sem rede)
│      │              │                                                       │
│   crypto.py: AESGCM (token) + RSA-OAEP (cartão)   ◄─ chaves SÓ via env      │
│      │              │                                                       │
│      ▼              ▼                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │ DB: merchant_subscriptions(+estado/token)  platform_charges       │     │
│   │     escrow_ledger   payment_webhook_events(UNIQUE idempotência)   │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│   webhooks/router.py  (PÚBLICO):                                           │
│     1. log webhook_logs  2. valida HMAC (compare_digest)                   │
│     3. dedup por (IdTransaction,status)  4. enfileira arq  5. 200 <5s      │
└───────────────────────────────┬────────────────────────────────────────────┘
                                │ enqueue (trabalho pesado)
                                ▼
                  arq WORKER (app/workers/)  — cron_jobs:
                    • charge_subscriptions_daily   (cobrança recorrente cartão)
                    • schedule_pix_charges         (agendamento PIX 3-5d antes)
                    • sync_delinquency             (10d→blocked, 20d→cancelado)
                    • release_escrow               (FINALIZADA+24h sem disputa)
                    • reconcile_safe2pay           (extrato × platform_charges)
                  reusa cron finalize_deliveries (Phase 9 → gatilho escrow)
```
Trace do caso primário (cobrança de entrega cartão): frontend cifra cartão (RSA-OAEP) → `POST /v1/deliveries` (Phase 7, agora ativando card/pix) → service descriptografa → `PaymentPort.charge_with_split(Amount=corrida+taxa, Splits=[entregador:corrida, jaxego:taxa+rev_share])` → grava `platform_charges` (idempotency key) → cria entrada `escrow_ledger` (HELD) → entrega nasce CRIADA. Webhook de pagamento confirma; `finalize_deliveries`+24h libera o escrow no saldo.

### Recommended Project Structure
```
apps/api/app/
├── payments/                 # NOVO — núcleo Safe2Pay
│   ├── __init__.py
│   ├── crypto.py             # AESGCM(token) + RSA-OAEP(cartão) + load keys de env
│   ├── port.py               # PaymentPort (Protocol) + dataclasses de resultado
│   ├── safe2pay_adapter.py   # impl httpx (_call_safe2pay + HasError + 3 subdomínios)
│   ├── safe2pay_stub.py      # Stub determinístico (dev/test, sem rede)
│   ├── factory.py            # get_payment_adapter() — Stub em dev/test (igual integrations)
│   ├── models.py             # platform_charges, escrow_ledger, payment_webhook_events
│   ├── subscriptions.py      # ativação/upgrade/downgrade + estados (estende Phase 4)
│   ├── escrow.py             # ledger: hold / release / freeze (RN-006)
│   ├── reconcile.py          # conciliação diária (D-08)
│   ├── router.py             # checkout, chave pública RSA, assinatura
│   ├── webhooks_router.py    # endpoints públicos Safe2Pay (HMAC + idempotência)
│   ├── schemas.py            # pydantic v2 (extra="forbid", tipos estreitos)
│   └── service.py            # orquestração de domínio
├── workers/                  # estende — novos cron_jobs (ver diagrama)
└── alembic/versions/0009_*.py  # migration reversível
```

### Pattern 1: PaymentPort (Protocol + httpx impl + Stub)
**What:** Interface própria (ADR-009 v2/D-09) idêntica ao padrão `app/integrations/base.py`.
**When to use:** Toda chamada a Safe2Pay. O `service` depende do Protocol, nunca da impl.
**Example:**
```python
# app/payments/port.py — Source: padrão de app/integrations/base.py [VERIFIED]
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class ChargeResult:
    transaction_id: str          # IdTransaction da Safe2Pay (idempotência)
    status: str                  # authorized | paid | refused | pending
    qr_code: str | None = None   # PIX
    token: str | None = None     # tokenização (None em sandbox — ver Pitfall 5)

@dataclass(frozen=True)
class Split:
    recipient: str               # subconta do entregador OU conta Jaxegô
    amount_cents: int            # SEMPRE centavos inteiros

class PaymentPort(Protocol):
    async def tokenize_card(self, card: "CardData") -> str | None: ...
    async def charge_with_token(self, *, token: str, amount_cents: int,
                                reference: str, customer: "Customer") -> ChargeResult: ...
    async def charge_with_split(self, *, amount_cents: int, splits: list[Split],
                                reference: str, method: str,
                                customer: "Customer") -> ChargeResult: ...
    async def create_pix_authorization(self, *, amount_cents: int,
                                       customer: "Customer", reference: str) -> ChargeResult: ...
    async def refund(self, *, transaction_id: str, amount_cents: int, method: str) -> None: ...
    async def register_subaccount(self, *, courier_id: int, mei_cnpj: str,
                                  pix_key: str) -> str: ...   # retorna recipient id
    async def get_statement(self, *, since, until) -> list["StatementEntry"]: ...
```

### Pattern 2: `_call_safe2pay` — HasError SEMPRE checado (skill safe2pay-escrow-br)
**What:** Helper central; resposta HTTP 200 da Safe2Pay NÃO significa sucesso.
**When to use:** Todo POST/GET ao Safe2Pay passa por aqui.
**Example:**
```python
# app/payments/safe2pay_adapter.py — Source: safe2pay-escrow-br SKILL.md:76-107 [VERIFIED]
async def _call_safe2pay(self, url: str, payload: dict) -> dict:
    assert_safe_url(url, allowlist=self._allowlist)          # A10 SSRF (app/integrations/http.py)
    async with build_client(timeout=httpx.Timeout(30.0)) as client:
        try:
            resp = await client.post(url, json=payload, headers=self._headers())
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("safe2pay_http_error", status=e.response.status_code)  # SEM payload (PII)
            raise PaymentGatewayError(f"Safe2Pay HTTP {e.response.status_code}") from e
        data = resp.json()
        if data.get("HasError"):                              # ⚠ ignora status HTTP
            code = data.get("ErrorCode", "unknown")
            logger.error("safe2pay_business_error", error_code=code)
            raise PaymentGatewayError(f"Safe2Pay {code}", code=code)
        return data.get("ResponseDetail", data)
```
3 base URLs no adapter (`PAYMENT_URL`/`API_URL`/`SERVICES_URL`) — `payment` cria, `api` administra (refund/subconta/saldo), `services` consulta. Nunca concatenar string de subdomínio (A1 da skill).

### Pattern 3: Criptografia em Python (adaptação Node→`cryptography`)
**What:** AES-256-GCM (token) + RSA-OAEP (cartão). A mecânica não muda; a lib sim.
**Example:**
```python
# app/payments/crypto.py — Source: ctx7 /pyca/cryptography aead.rst + rsa.rst [VERIFIED]
import os, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidTag

def _token_key() -> bytes:
    hexkey = settings.safe2pay_token_encrypt_key          # 64 hex chars = 32 bytes
    if not hexkey or len(hexkey) != 64:
        raise RuntimeError("SAFE2PAY_TOKEN_ENCRYPT_KEY inválida (64 hex)")
    return bytes.fromhex(hexkey)

def encrypt_token(plain: str) -> str:
    # ⚠ no cryptography, encrypt() já ANEXA a tag de 16 bytes ao fim do ciphertext.
    # Formato: base64( nonce[12] + ciphertext_que_inclui_tag[16 no fim] )
    aesgcm = AESGCM(_token_key())
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plain.encode(), None)        # ct = real_ct || tag(16)
    return base64.b64encode(nonce + ct).decode()

def decrypt_token(blob: str) -> str:
    raw = base64.b64decode(blob)
    nonce, ct = raw[:12], raw[12:]                          # ct ainda inclui a tag
    try:
        return AESGCM(_token_key()).decrypt(nonce, ct, None).decode()
    except InvalidTag as e:
        raise RuntimeError("token corrompido/adulterado") from e   # NÃO retornar o blob

def rsa_decrypt_card(b64_ciphertext: str) -> str:
    pem = settings.rsa_private_key
    if not pem.startswith("-----"):
        pem = base64.b64decode(pem).decode()
    key = serialization.load_pem_private_key(pem.encode(), password=None)
    plain = key.decrypt(
        base64.b64decode(b64_ciphertext),
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    return plain.decode()   # JSON: {nomeTitular, numeroCartao, validade, cvv} — NUNCA logar
```

### Pattern 4: Webhook idempotente (logar → validar HMAC → dedup → enfileirar → 200)
**What:** Endpoint público; ordem é obrigatória (skill A3/A4 + owasp A08).
**Example:**
```python
# app/payments/webhooks_router.py — Source: safe2pay-escrow-br:219-261 + owasp A08 [VERIFIED]
@router.post("/webhooks/safe2pay", status_code=200)
async def safe2pay_webhook(request: Request, db = Depends(get_db)):
    body = await request.body()
    await log_webhook(db, payload=body)                    # 1. SEMPRE logar antes (sem PII de cartão)
    sig = request.headers.get("x-safe2pay-signature")      # [ASSUMIDO] header — confirmar (LOW)
    if not _verify_hmac(body, sig):                        # 2. compare_digest, NUNCA ==
        logger.warning("safe2pay_webhook_bad_signature")
        raise HTTPException(403, "assinatura inválida")
    payload = json.loads(body)
    tx, status = _extract(payload, "IdTransaction"), _extract(payload, "Status")
    if await already_processed(db, tx, status):            # 3. UNIQUE(tx, status) idempotência
        return {"ok": True, "idempotent": True}
    await enqueue("process_safe2pay_event", tx=tx, status=status, payload=payload)  # 4. fila
    return {"ok": True}                                    # 5. 200 < 5s
```

### Anti-Patterns to Avoid
- **Cartão/CVV/token em texto puro em log ou banco:** FAIL-BLOCK (A09). Cartão só RSA→memória→Safe2Pay; token só AES-256-GCM.
- **Float para dinheiro:** sempre centavos inteiros (Phase 7 / DRV-009). Arredondamento de split em centavos (TH-F).
- **Replicar o layout `iv+tag+ct` do Node literalmente:** no `cryptography` a tag já vem no fim do ciphertext (Pitfall 1).
- **Processar webhook antes de validar HMAC:** A08. Validar primeiro, qualquer efeito depois.
- **`==` na comparação de assinatura:** timing attack — `secrets.compare_digest` (A02/A08).
- **Chamar Safe2Pay dentro de transação de banco aberta:** lock bloqueante (skill anti-pattern).
- **Retornar 500 no webhook em erro de negócio:** Safe2Pay reenvia indefinidamente. Logar, enfileirar, 200.
- **Taxa/split calculado no frontend:** backend é a autoridade (A04 + skill A5).
- **Cobrança recorrente com token em sandbox:** não funciona; só produção (Pitfall 5).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| AES-256-GCM / RSA-OAEP | Cifra própria / `==` de tag | `cryptography` `AESGCM` + `padding.OAEP` | Tag auth, nonce, padding OAEP são sutis; lib oficial PyCA já validada |
| SSRF guard de saída | Validação de host ad-hoc | `assert_safe_url` (app/integrations/http.py) | Já resolve DNS, rejeita IP privado, revalida pós-redirect (A10) |
| Adapter pattern + Stub | Mock manual por teste | Padrão `base.py`/`factory.py` (Stub em dev/test) | Testes nunca tocam rede; troca de PSP é trocar impl (D-09) |
| Cron/scheduler | Loop/thread próprio | `arq` `cron_jobs` (já configurado) | Idempotência, Redis, retry; `finalize_deliveries` já existe |
| Idempotência de webhook | Flag em memória | Tabela `payment_webhook_events` UNIQUE(tx,status) | Memória não sobrevive a reinício/multi-worker (skill A3) |
| aware-UTC datetime | `datetime.now()` naive | `UTC_DATETIME` mixin + `ensure_aware_utc` | TD-010 — naive datetime é risco recorrente auditado |
| HMAC compare | `sig == expected` | `secrets.compare_digest` | Timing attack |

**Key insight:** Em pagamento, "quase certo" é dinheiro perdido ou vazado. Toda primitiva de segurança/idempotência já existe no projeto ou na stdlib/lib oficial — hand-roll aqui é a forma mais cara de errar.

## Runtime State Inventory

> Phase greenfield em termos de dados (cria tabelas novas), MAS toca estado de runtime em integração externa e config. Não-vazio.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `merchant_subscriptions` (Phase 4) hoje só tem `status` (active/pending/canceled) — Phase 10 precisa estender com estado de cobrança (trial/active/blocked/cancelado), token AES, dt_vencimento, método. `couriers.mei_cnpj`/`mei_pending` (Phase 5) viram gancho de subconta. `deliveries.payment_method` enum já tem `card`/`pix` (aceitos, rejeitados em Phase 7) — agora ativados. | migration 0009 + code edit |
| Live service config | **Safe2Pay (externo):** subcontas de entregadores cadastradas no painel/API Safe2Pay NÃO vivem no git. URLs de webhook precisam ser registradas no painel Safe2Pay (`POST {dominio}/v1/webhooks/safe2pay`). `[ASSUMIDO]` split/marketplace habilitado na conta contratada (DEC-003 — confirmar). | registro manual no painel + ADR de confirmação |
| OS-registered state | Cron diário precisa de gatilho: o projeto usa `arq cron_jobs` (in-process), não cron do OS. Nenhum task scheduler de OS. | nenhum — usar arq cron |
| Secrets/env vars | NOVOS segredos: `SAFE2PAY_API_KEY`, `SAFE2PAY_SANDBOX`, `SAFE2PAY_TOKEN_ENCRYPT_KEY` (64 hex), `RSA_PRIVATE_KEY`, `RSA_PUBLIC_KEY`, `SAFE2PAY_WEBHOOK_SECRET` (HMAC, `[ASSUMIDO]`), URLs/allowlist de subdomínios Safe2Pay. Todos via env (Gate 8 FAIL-BLOCK se no repo). `.env.example` com placeholders. | adicionar a `config.py` (Field default None p/ segredos) + `.env.example` |
| Build artifacts | Nenhum artefato instalável renomeado. | None — verificado: sem egg-info/binário afetado |

**Canonical question — após todos os arquivos atualizados, o que tem estado fora do git?** (a) subcontas e config de split no painel Safe2Pay; (b) URLs de webhook registradas no painel; (c) os 6+ segredos no `.env` de produção. Todos devem entrar no checklist de deploy da phase.

## Common Pitfalls

### Pitfall 1: Layout do AES-GCM Node ≠ Python (tag embutida)
**What goes wrong:** SAAS-BILLING especifica `base64(iv[12]+tag[16]+ct)` porque no `node:crypto` a tag é obtida separadamente (`cipher.getAuthTag()`). No `cryptography` Python, `aesgcm.encrypt()` **já retorna o ciphertext com a tag de 16 bytes anexada ao FINAL**. Replicar o layout Node literalmente quebra decrypt.
**Why it happens:** Porte 1:1 sem ler a API da lib.
**How to avoid:** Padronizar `base64(nonce[12] + ciphertext_da_lib)` onde `ciphertext_da_lib` já inclui a tag. Não tentar separar/reordenar tag. Documentar no docstring. Teste round-trip obrigatório. `[VERIFIED: ctx7 /pyca/cryptography]`
**Warning signs:** `InvalidTag` em todo decrypt; tentativa de fatiar `[12:28]` como tag.

### Pitfall 2: HTTP 200 da Safe2Pay tratado como sucesso (`HasError`)
**What goes wrong:** Transação nunca criada, mas código acha que deu certo; entrega nasce sem cobrança.
**Why/avoid:** `_call_safe2pay` central que SEMPRE checa `data["HasError"]` (skill A2). Nunca chamar Safe2Pay sem o helper.
**Warning signs:** `resp.raise_for_status()` sem checagem de `HasError` depois.

### Pitfall 3: Webhook duplicado processado 2× (dupla baixa/liberação)
**What goes wrong:** Safe2Pay reenvia; escrow liberado 2×, cobrança marcada paga 2×.
**Why/avoid:** Tabela `payment_webhook_events` UNIQUE(`transaction_id`,`status`); checar antes de qualquer efeito (skill A3).
**Warning signs:** Flag em memória; ausência de constraint UNIQUE.

### Pitfall 4: Naive datetime em vencimento/escrow/cron (TD-010)
**What goes wrong:** `grace_boundary.replace(tzinfo=None)` — mistura naive/aware, cálculo de 24h/10d/20d errado. Lição de campo auditada (TD-010, pre_launch_high).
**Why/avoid:** Vencimentos, escrow 24h, janelas de inadimplência e cron SEMPRE em aware-UTC (`_utcnow`, `ensure_aware_utc`, `UTC_DATETIME`). Conversão para America/Sao_Paulo só na borda de exibição.
**Warning signs:** `datetime.now()` sem tz; `.replace(tzinfo=None)` em domínio.

### Pitfall 5: Token de cartão em sandbox (não funciona)
**What goes wrong:** Em sandbox, Safe2Pay **não retorna token** — cobra raw. Cobrança recorrente com token só funciona em produção. Testar recorrência em sandbox falha silenciosamente.
**Why/avoid:** `processar_cartao` trata sandbox (cobra raw) vs produção (tokeniza→cobra). Cobrança recorrente e link de cobrança SEMPRE `IsSandbox: false`, mesmo com `SAFE2PAY_SANDBOX=true` (SAAS-BILLING §13). **Nos testes, usar o Stub — NUNCA chamar Safe2Pay real nem sandbox** (D-09).
**Warning signs:** Teste de cron de cobrança batendo em URL Safe2Pay; `token=None` tratado como erro em vez de fluxo sandbox.

### Pitfall 6: Split com soma ≠ Amount (arredondamento em centavos)
**What goes wrong:** `Amount` ≠ Σ splits por arredondamento de revenue share (ex.: 20% de R$2,00 = R$0,40 ok, mas 20% de R$1,99 dá fração). Safe2Pay rejeita ou desconcilia.
**Why/avoid:** Calcular em centavos inteiros; a sobra de arredondamento vai para a conta Jaxegô (residual determinístico). Invariante testado: `amount_cents == sum(s.amount_cents for s in splits)` (TH-F).
**Warning signs:** Float no split; soma divergente em teste.

### Pitfall 7: Migration 0009 com revision id longo / não-reversível
**What goes wrong:** Lição Phase 9. Convenção do projeto usa ids descritivos (`0008_proofs_tracking_notif`). Manter o padrão `0009_<slug_curto>` e `down_revision = "0008_proofs_tracking_notif"`. Garantir `downgrade()` que dropa as tabelas novas (reversível).
**Why/avoid:** Manter slug curto e legível; testar `alembic downgrade -1` e `upgrade head` no CI.
**Warning signs:** `downgrade()` vazio; revision id excessivamente longo.

## Code Examples

### Cobrança split por entrega (D-05 / REQ-034) — `[ASSUMIDO]` formato Safe2Pay (DEC-003)
```python
# app/payments/service.py — Source: integracoes.md §1 + skill safe2pay-escrow-br [VERIFIED rule, ASSUMED API shape]
async def charge_delivery(self, *, delivery, courier, merchant) -> ChargeResult:
    corrida_cents = delivery.fee_quote_cents              # corrida do entregador
    taxa_cents    = self._platform_fee_cents(merchant)    # taxa do plano (seed, não hardcoded)
    rev_share_cents = self._revenue_share_cents(delivery.area_id, taxa_cents)  # OQ-1 default 20% [ASSUMIDO]
    splits = [
        Split(recipient=courier.s2p_recipient_id, amount_cents=corrida_cents),       # escrow entregador
        Split(recipient=settings.s2p_jaxego_recipient, amount_cents=taxa_cents),      # conta Jaxegô (+rev share embutido)
    ]
    assert corrida_cents + taxa_cents == sum(s.amount_cents for s in splits)  # TH-F invariante
    reference = f"dlv_{delivery.id}"                       # idempotência de negócio (Reference)
    result = await self._payment.charge_with_split(
        amount_cents=corrida_cents + taxa_cents, splits=splits,
        reference=reference, method=delivery.payment_method, customer=...)
    # platform_charges com idempotency key + IdTransaction; escrow_ledger HOLD da corrida
    await self._record_charge_and_hold(delivery, result, corrida_cents, taxa_cents)
    return result
```

### Escrow interno: hold → release (D-06 / REQ-036)
```python
# app/payments/escrow.py — Source: RN-006 + reusa finalize_deliveries (Phase 9) [VERIFIED]
async def release_escrow(ctx) -> int:
    """Cron: libera corridas FINALIZADA há ≥24h sem disputa aberta. aware-UTC (TD-010)."""
    cutoff = datetime.now(UTC) - timedelta(hours=24)
    rows = await repo.holds_ready_for_release(finalized_before=cutoff)  # WHERE finalized_at<=cutoff AND no open dispute
    released = 0
    for hold in rows:
        async with db.begin():                            # atômico: ledger + saldo
            await repo.mark_released(hold.id)             # idempotente: só se ainda HELD
            await repo.credit_courier_balance(hold.courier_id, hold.amount_cents)
        released += 1
    return released
# Disputa aberta dentro das 24h → FREEZE só daquela entrega (F-07 E4); demais seguem.
```

### Inadimplência (D-03 / SAAS-BILLING §10) — aware-UTC
```python
# app/payments/subscriptions.py — Source: SAAS-BILLING §10 (adaptado p/ aware-UTC) [VERIFIED]
GRACE_BLOCK_DAYS, GRACE_CANCEL_DAYS = 10, 20   # seed/config se parametrizável

def classify_delinquency(days_overdue: int) -> str:
    if days_overdue > GRACE_CANCEL_DAYS: return "cancelado"
    if days_overdue > GRACE_BLOCK_DAYS:  return "blocked"
    return "active"

def days_overdue(due_at: datetime | None, now: datetime) -> int:
    if due_at is None: return 0
    due = ensure_aware_utc(due_at)                 # TD-010
    return max(0, (now.date() - due.date()).days)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pagar.me (ADR-009 v1) | Safe2Pay (ADR-009 v2) | adrs.md | Endpoints/payloads desta phase são Safe2Pay |
| `node:crypto` (SAAS-BILLING ref) | `cryptography` Python | esta phase | Format AES-GCM ajustado (Pitfall 1); RSA-OAEP idêntico em semântica |
| Escrow nativo do PSP | Escrow interno de domínio 24h | RN-006/DEC-003 | Ledger Jaxegô controla liberação, independente do PSP |
| `payment_method` card/pix "em breve" (Phase 7) | card/pix ativos com cobrança+split | esta phase | Phase 7 reaberto para os dois métodos |

**Deprecated/outdated:** Pagar.me (rejeitado). `decryptToken` que retorna o blob cru em falha (SAAS-BILLING §4.1 "legado em texto puro") — **NÃO portar**: em Python, `InvalidTag` deve levantar erro, não retornar o blob (não há legado em texto puro num projeto greenfield).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Split/marketplace disponível no plano Safe2Pay contratado | D-05 / REQ-034 | ALTO — se indisponível, split inteiro precisa de outra estratégia (ex.: transfer pós-cobrança). Interface própria mitiga |
| A2 | Formato exato do payload de Split na API Safe2Pay (`Splits:[{Recipient,Amount}]`) | Code Examples | MÉDIO — shape pode diferir; adapter isola, mas testes do shape precisam revisão com Postman/contrato |
| A3 | Subconta/recipient cadastrável via API (`register_subaccount`) e id retornado | D-07 / REQ-019 | MÉDIO — pode exigir cadastro manual no painel; gancho MEI permanece válido |
| A4 | Safe2Pay fornece HMAC-SHA256 de webhook via header (`x-safe2pay-signature`) | Webhook / D-04 | ALTO p/ segurança — SAAS-BILLING §13 marca como "validação futura/recomendada". Se ausente, mitigar com allowlist de IP + idempotência + segredo em path (ver TH-E) |
| A5 | Prazo de repasse de subconta do PSP | D-01 / escrow | BAIXO — escrow interno de 24h é independente do prazo do PSP por decisão (DEC-003) |
| A6 | Taxa por transação parametrizável (não fixa pelo PSP) | D-01 | BAIXO — implementada como seed/config; só muda o valor |
| A7 | Revenue share default 20% (OQ-1) | D-05 | BAIXO — parametrizado por área; default trocável sem código |
| A8 | Cálculo anual = `preco_mensal × 10` (2 meses grátis) | Assinatura | BAIXO — política de desconto é seed; ajustar conforme produto |
| A9 | Endpoints de estorno: Pix `api/v2/Transaction/Refund`, Cartão `api/v2/CreditCard/Reverse` | Estornos / D-08 | MÉDIO — skill marca "aguardar Postman do Cadu"; adapter isola |

**DEC-003 trava:** A1–A3, A9 são os pontos que o contrato real Safe2Pay precisa confirmar. ADR de confirmação supera DEC-003 quando o contrato chegar.

## Open Questions

1. **Split disponível e seu formato exato na API Safe2Pay (A1/A2)** — *bloqueia REQ-034.*
   - Sabemos: split é requisito (integracoes.md §1); implementado parametrizado atrás de interface.
   - Não sabemos: se o plano contratado habilita marketplace; shape do payload.
   - Recomendação: Regra 12 → **task explícita** "validar split no contrato/Postman" com critério de aceite; até lá, Stub define o shape e o adapter httpx fica `[ASSUMIDO]`. REQ-034 AC explícito: "`[DECIDIR]` validado (bloqueia execução desta funcionalidade)".

2. **HMAC de webhook fornecido pela Safe2Pay? (A4)** — *segurança.*
   - Sabemos: SAAS-BILLING §13 marca como "validação futura recomendada"; skill exige HMAC.
   - Não sabemos: se Safe2Pay assina o webhook nativamente.
   - Recomendação: Regra 12 → **task** "confirmar HMAC Safe2Pay". Mitigação de defesa em profundidade enquanto incerto (ver TH-E): idempotência + allowlist de IP de origem + segredo no path do webhook + nunca liberar dinheiro só por webhook sem consulta de status (`GET /v2/Transaction/{id}`).

3. **Cadastro de subconta via API ou manual (A3)** — *REQ-019.*
   - Recomendação: implementar `register_subaccount` no port; se a API não suportar, o Stub/adapter degrada para "marca pendência de cadastro manual" e o gancho MEI permanece.

4. **Endpoints exatos de estorno (A9)** — skill diz "aguardar Postman do Cadu".
   - Recomendação: TD ou task de confirmação; adapter isola as URLs por subdomínio.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `cryptography` | crypto.py (AES-GCM/RSA-OAEP) | ✓ | 43–45 (pyproject) | — |
| `httpx` | Safe2PayHttpAdapter | ✓ | 0.28+ | Stub em dev/test |
| `arq` + Redis | crons de cobrança/escrow/conciliação | ✓ | 0.26 / redis | — |
| MySQL 8 | platform_charges, escrow_ledger, webhook_events | ✓ | 8 | SQLite em test |
| Conta Safe2Pay (sandbox + produção) | impl real (staging/prod) | ✗ (não verificável aqui) | — | **Stub em dev/test** (D-09) — execução da phase NÃO depende da conta real; produção sim |
| Painel Safe2Pay (subcontas, webhooks, split habilitado) | produção | ✗ `[ASSUMIDO]` | — | registro manual + ADR de confirmação (DEC-003) |

**Missing dependencies with no fallback:** nenhum bloqueia a *implementação* (Stub cobre dev/test). **Para produção**, a conta Safe2Pay com split habilitado é pré-requisito não verificável agora (DEC-003).
**Missing dependencies with fallback:** conta/painel Safe2Pay → Stub para todo dev/test; produção exige config real via env + painel.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (padrão do projeto; tests/ existente) |
| Config file | `apps/api/pyproject.toml` (pytest config) |
| Quick run command | `cd apps/api && uv run pytest tests/payments -x -q` |
| Full suite command | `cd apps/api && uv run pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-034 | charge_with_split soma exata + Reference idempotente + recusa→não nasce | unit | `pytest tests/payments/test_split.py -x` | ❌ Wave 0 |
| REQ-034 | HasError da Safe2Pay levanta PaymentGatewayError (não cria charge órfã) | unit | `pytest tests/payments/test_adapter_haserror.py -x` | ❌ Wave 0 |
| REQ-010 | tokeniza→cobra; webhook recorrente idempotente | unit | `pytest tests/payments/test_subscription.py -x` | ❌ Wave 0 |
| REQ-010/D-04 | webhook duplicado → 1 efeito; HMAC inválido → 403 | integration | `pytest tests/payments/test_webhooks.py -x` | ❌ Wave 0 |
| REQ-036 | release_escrow só FINALIZADA+24h sem disputa; disputa congela só a entrega | unit | `pytest tests/payments/test_escrow.py -x` | ❌ Wave 0 |
| REQ-029 | estorno só da própria cobrança (ownership); valor RN-004 | unit | `pytest tests/payments/test_refund.py -x` | ❌ Wave 0 |
| REQ-011 | upgrade pro-rata em centavos; downgrade agendado | unit | `pytest tests/payments/test_plan_change.py -x` | ❌ Wave 0 |
| D-02 | round-trip AES-256-GCM + RSA-OAEP; InvalidTag levanta | unit | `pytest tests/payments/test_crypto.py -x` | ❌ Wave 0 |
| D-03 | inadimplência 10→blocked/20→cancelado com aware-UTC | unit | `pytest tests/payments/test_delinquency.py -x` | ❌ Wave 0 |
| D-08 | conciliação detecta divergência >R$0,01 | unit | `pytest tests/payments/test_reconcile.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/payments -x -q`
- **Per wave merge:** `uv run pytest -q` (suite completa, isolamento de área incluso)
- **Phase gate:** suite verde + `alembic upgrade head && alembic downgrade -1` reversível antes de `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/payments/conftest.py` — fixture `PaymentStubAdapter` + factory override (NUNCA rede)
- [ ] `tests/payments/test_crypto.py` — round-trip + InvalidTag
- [ ] `tests/payments/test_adapter_haserror.py` — HasError = 200 mas falha
- [ ] `tests/payments/test_split.py`, `test_escrow.py`, `test_refund.py`, `test_webhooks.py`, `test_subscription.py`, `test_delinquency.py`, `test_reconcile.py`, `test_plan_change.py`
- [ ] Lint custom de naive datetime cobrindo `app/payments/*` (TD-010)

## Security Baseline (Gate 4 — OBRIGATÓRIA · é DINHEIRO · exaustiva)

> Threat model curto (owasp A04): **quem pode abusar?** atacante de rede (webhook forjado), insider/cliente malicioso (estorno/cobrança de terceiro), erro de concorrência (dupla cobrança/liberação), PSP/contrato divergente (split/conciliação). **O que ganha?** dinheiro liberado sem pagamento, dados de cartão, dupla cobrança. **Pior caso:** liberação de escrow sem pagamento real, vazamento de cartão (PCI-adjacent), perda financeira por conciliação cega.

| # | Ameaça | STRIDE | Mitigação (cita owasp + SAAS-BILLING) |
|---|--------|--------|----------------------------------------|
| TH-A | **Dados de cartão em texto puro / em log** (PCI-adjacent) | Info Disclosure | Frontend cifra com **RSA-OAEP-2048** (chave pública via GET); backend decifra só em memória com `RSA_PRIVATE_KEY` (SÓ env) e envia direto à Safe2Pay. `{numeroCartao,cvv,validade}` NUNCA persistidos, NUNCA logados. Filtro structlog central mascara `card`/`cvv`/`numeroCartao`. `[owasp A09 + A02; SAAS-BILLING §4.2/§13]` |
| TH-B | **Token de cartão em repouso** legível | Info Disclosure / Tampering | **AES-256-GCM** (`base64(nonce12+ct_com_tag)`); `SAFE2PAY_TOKEN_ENCRYPT_KEY` 32 bytes SÓ env. Decifrar SOMENTE no cron de cobrança. `InvalidTag` → erro, nunca retorna blob. `[owasp A02; SAAS-BILLING §4.1/§13]` |
| TH-C | **Segredos no repo** (`SAFE2PAY_API_KEY`, chaves cripto, webhook secret) | Info Disclosure | Todos via env (`Field default None` em `config.py`); `.env.example` com placeholders; `.env` no `.gitignore` desde o 1º commit. Segredo commitado = **ROTACIONAR** (não basta remover do histórico). Gate 8 FAIL-BLOCK. `[owasp Gestão de Segredos; SAAS-BILLING §11/§13]` |
| TH-D | **Dupla cobrança / cobrança duplicada** (idempotência) | Tampering / Repudiation | TODA escrita de cobrança com idempotency key + `Reference`/`IdTransaction`. `platform_charges` UNIQUE por idempotency key. Webhook UNIQUE(`transaction_id`,`status`). Recobrança só se charge ainda `aberto`. `[owasp A08; skill A3; integracoes.md §1]` |
| TH-E | **Webhook forjado / sem auth** (libera dinheiro falso) | Spoofing / Tampering | Ordem obrigatória: logar → **validar HMAC-SHA256** com `secrets.compare_digest` (NUNCA `==`) → deduplicar → enfileirar → 200. `[ASSUMIDO A4]` se Safe2Pay não fornecer HMAC: defesa em profundidade — allowlist de IP de origem + segredo no path + **nunca liberar escrow só pelo webhook**: confirmar via `GET /v2/Transaction/{id}` antes de qualquer efeito financeiro. Anti-replay (janela/timestamp). `[owasp A08/A01; skill A4; SAAS-BILLING §13]` |
| TH-F | **Integridade do split** (soma ≠ Amount, arredondamento) | Tampering | Split SEMPRE no backend (frontend nunca manda valores — A04). Centavos inteiros; invariante `amount_cents == Σ splits` testado; residual de arredondamento determinístico → conta Jaxegô. Revenue share parametrizado por área (seed). `[owasp A04; skill A5; DRV-009]` |
| TH-G | **Escrow liberado cedo / indevido** | Elevation / Tampering | Release SÓ via cron `release_escrow` com `FINALIZADA (Phase 9) + 24h aware-UTC + sem disputa aberta`. Nunca via endpoint do usuário (skill state machine). Disputa nas 24h → FREEZE só daquela entrega. Transição atômica (ledger + saldo no mesmo commit). Idempotente (só libera se ainda HELD). `[owasp A01/A08; skill state machine; RN-006/F-07 E4]` |
| TH-H | **Estorno de cobrança alheia (IDOR) / valor errado** | Elevation / Tampering | Estorno escopado: `repo.get_charge_for_tenant(charge_id, area_id=user.area_id)` no WHERE (não em `if`); 404 (não 403) p/ outro escopo. Valor do estorno calculado no backend conforme RN-004 (pré-aceite total; pós-aceite 50%; pós-coleta 100%+retorno). Só estorna charge em estado estornável. `[owasp A01; RN-004; skill A7 estorno parcial]` |
| TH-I | **Conciliação cega** (divergência extrato × registros) | Repudiation / Tampering | Job diário compara extrato Safe2Pay (`get_statement`) × `platform_charges`; diferença **>R$0,01** → alerta admin plataforma (não auto-corrige). Money em centavos; comparação exata. `[owasp A08; integracoes.md §1; D-08]` |
| TH-J | **Race em cobrança / liberação** (execução paralela do cron) | Tampering | Lock/idempotência: cron idempotente (estado-guard: só processa `situacao=0`/`HELD`); `SELECT ... FOR UPDATE` ou flag de execução; UNIQUE constraints impedem efeito duplo mesmo sob race. `[owasp A08; SAAS-BILLING §7 flag executando]` |
| TH-K | **PII/LGPD de cobrança** (CPF/CNPJ, e-mail, telefone do pagador) | Info Disclosure | CPF/CNPJ de cobrança mascarados em output, NUNCA em log (filtro central). `documento_cobranca` é tratamento de dado pessoal: base legal (execução de contrato), retenção definida, entra em pedido de eliminação. Dado fiscal preservado sem PII (RN-021). `[owasp A09 + LGPD; br/lgpd-compliance; RN-021]` |
| TH-L | **SSRF na chamada ao PSP / redirect** | (A10) | `assert_safe_url` com allowlist dos 3 subdomínios Safe2Pay antes de conectar e pós-redirect; `build_client(follow_redirects=False)`. `[owasp A10; app/integrations/http.py]` |
| TH-M | **Endpoint sem decisão de auth** | (A01) | Checkout/assinatura: `Depends(get_current_user)` + escopo de merchant/área. Webhooks/chave-pública-RSA: `# público: <justificativa>` explícito (assinatura/idempotência cobrem). Cron: Bearer `CRON_API_KEY` OU arq in-process (sem rota pública). `[owasp A01; SAAS-BILLING §9/§12]` |

**Threat model herda para o PLAN.md (Regra 7):** o `threat_model` do PLAN copia TH-A..TH-M como itens verificáveis no `secure-phase`.

## Sources

### Primary (HIGH confidence)
- `docs/SAAS-BILLING-DOCS.md` (lei de billing, §4 cripto / §5 endpoints / §7 cron / §8 webhooks / §10 inadimplência / §13 segurança) — lido inteiro
- `.claude/skills/domain/safe2pay-escrow-br/SKILL.md` (546 linhas) — HasError, subdomínios, idempotência, HMAC, estados de escrow, estorno
- `.claude/skills/owasp-security/SKILL.md` (A01–A10 + segredos + LGPD)
- ctx7 `/pyca/cryptography` — `AESGCM` (aead.rst) + `padding.OAEP` (rsa.rst): API e formato verificados
- Código existente: `app/integrations/{base,factory,http,receita}.py`, `app/core/config.py`, `app/db/mixins.py`, `app/workers/settings.py`, `app/plans/models.py`, `app/merchants/models.py`, `app/payments_direct/models.py`, `app/deliveries/models.py`, `app/couriers/models.py` (MEI)
- `projeto/docs-externos/integracoes.md` §1; `projeto/regras-negocio/{regras.md (RN-004/006/010/021/023/029), fluxos.md (F-03/F-07), entidades.md (Financeiro)}`
- `.planning/DECISIONS.md` (ADR-009 v2, DEC-003); `.planning/REQUIREMENTS.md` (REQ-010/011/019/034/036/029); `.planning/TECH-DEBT.md` (TD-010)

### Secondary (MEDIUM confidence)
- Convenção alembic do projeto (revision ids descritivos, `0008_proofs_tracking_notif`) — inferida dos arquivos

### Tertiary (LOW confidence — marcadas `[ASSUMIDO]` / DEC-003)
- Formato exato de Split/subconta na API Safe2Pay; disponibilidade de marketplace; HMAC nativo de webhook; endpoints exatos de estorno; prazo de repasse; taxa — **aguardam contrato/Postman real** (Assumptions Log A1–A9)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — todas as libs já no projeto e versões verificadas; cripto confirmada na lib oficial
- Arquitetura (PaymentPort/Stub, escrow ledger, webhooks): HIGH no padrão (replica `app/integrations/`); MEDIUM no schema (discrição)
- Mecânica de assinatura/cripto/inadimplência: HIGH (SAAS-BILLING é lei + verificada)
- Contrato Safe2Pay (split/subconta/HMAC/estorno/prazo/taxa): LOW — DEC-003 `[ASSUMIDO]`, atrás de interface própria
- Pitfalls: HIGH (skill + lib + lição de campo TD-010)

**Research date:** 2026-06-11
**Valid until:** mecânica/cripto 30 dias (estável); itens `[ASSUMIDO]` até o contrato Safe2Pay real chegar (ADR supera DEC-003)
