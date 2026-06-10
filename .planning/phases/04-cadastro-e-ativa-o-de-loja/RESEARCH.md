# Phase 4: Cadastro e ativação de loja - Research

**Researched:** 2026-06-10
**Domain:** Cadastro multi-step de loja (PII BR), integrações externas via adapter (Receita/SMS/SES/geocoding), máquina de estados de merchant, jobs de revalidação (arq), seeds idempotentes
**Confidence:** HIGH (stack e padrões reusados da Phase 2); MEDIUM/LOW para contratos de APIs externas (ver Assumptions Log)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Wizard de cadastro: dados da conta (CNPJ ou CPF p/ autônomo, nome fantasia, categoria, telefone E.164, e-mail, senha argon2id) → confirmação e-mail (link) + telefone (SMS OTP) → endereço (geocodifica → vincula à área) → escolha de plano (Free pré-selecionado). [auto] (F-01 passos 1-7).
- **D-02:** Anti-duplicidade (RN-011): CNPJ/CPF + telefone + e-mail únicos por tipo de conta. Colisão → mensagem anti-enumeração ("Já existe conta com esse dado. Recuperar acesso?") sem dizer QUAL dado colidiu além do informado.
- **D-03:** CNPJ validado na Receita (situação ativa) antes de ativar loja. Provider: minhareceita.org self-hosted primário + BrasilAPI fallback (DRV-006), atrás de interface/adapter própria. Em DEV/teste: adapter stub configurável (não chamar API real nos testes).
- **D-04:** Exceções: CNPJ inativo/inexistente (E1) → bloqueia com mensagem clara + suporte. Receita fora do ar (E4) → cadastro segue `pending_validation`, loja usa Free com limite, revalidação por job (retry 6/6/12/24h).
- **D-05:** Status do merchant: `pending_payment`, `pending_validation`, `active`, `suspended`. Geocodificação sem área cobrindo → tela "Ainda não chegamos aí" + captura de interesse (e-mail+cidade) [estado vazio obrigatório].
- **D-06:** Seeds de `subscription_plans`: Free (R$0, 2 entregas/mês, taxa R$2,00), Início, Profissional, Sem Limite — valores `[ASSUMIDO]` implementados como SEEDS EDITÁVEIS (DRV-009), NUNCA hardcoded. Plano Free é seed imutável.
- **D-07:** Nesta phase, só o caminho Free é ativável de fato (cria `merchant_subscriptions` Free ativo). Plano pago → cria merchant em `pending_payment` e mostra aviso persistente; checkout Safe2Pay real é a Phase 10.
- **D-08:** Confirmação de telefone via SMS OTP (Zenvia primário + Twilio fallback, DRV-007) atrás de adapter; confirmação de e-mail via AWS SES (link). Em DEV/teste: adapters stub (log/captura, sem envio real). Quota de SMS por plano.
- **D-09:** Seed inicial: área **Pádua** (codename `padua`, nível KYC, piso, geofence default), os 4 planos, e um **admin de plataforma** + **admin de área** de bootstrap (CLI/script idempotente).

### Claude's Discretion
- Geocoding provider (Nominatim/OSM ou similar) atrás de adapter.
- Estrutura do wizard no frontend (stepper) e persistência de progresso parcial.
- Formato exato dos seeds (script Python `seed.py` vs migration de dados).

### Deferred Ideas (OUT OF SCOPE)
- Checkout pago real via Safe2Pay (cartão/PIX recorrente) — Phase 10.
- Cadastro/KYC de entregador — Phase 5.
- Criação de entregas — Phase 7.
- Limite de plano enforçado na criação de entrega (RN-028) — Phase 7 (aqui só o seed do limite).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-008 | F-01 completo com 4 exceções (E1-E4) | Máquina de estados de merchant + adapter Receita (stub/real) + job de revalidação arq (§Abordagem técnica) |
| REQ-009 | Seeds de planos `[ASSUMIDO]` editáveis (DRV-009) | Seeds idempotentes via script `seed.py` (§Seeds idempotentes) |
| REQ-006 | Anti-duplicidade aplicada (RN-011) | Reuso do padrão anti-enumeração da Phase 2 (`auth/service.py`); UNIQUE por tipo de conta + resposta constante (§Security Baseline T1) |
</phase_requirements>

## Summary

Phase 4 implementa o fluxo F-01 de cadastro de loja end-to-end no caminho Free, com 4 exceções (CNPJ inativo, colisão anti-enumeração, pagamento falha→Free, Receita fora→pending_validation). A boa notícia: **a Phase 2 já entregou quase toda a infraestrutura de segurança** que esta phase precisa — argon2id, anti-enumeração com tempo ~constante (`auth/service.py`), aware UTC com microssegundos (TD-010 já resolvido em `db/mixins.py`), logging JSON sem PII (`core/logging.py` + denylist em `config.json > observability.pii_fields_forbidden_in_logs`), RFC-7807 errors, `AreaScopedMixin`, e o worker arq (`workers/`) já booteia. O trabalho desta phase é **somar entidades de domínio e adapters de integração**, não reinventar a base de segurança.

O risco central não é técnico-de-base, é **integração externa**: Receita Federal, SMS (Zenvia/Twilio), SES e geocoding. A abordagem obrigatória é o **padrão adapter** — uma interface (Protocol) por integração, uma implementação real (httpx async, já no toolchain), e um **stub configurável para dev/teste** que NUNCA chama a rede. Isso permite que o Gate 5 (integration-checker) valide o contrato (forma do request/response) com stubs, e que a suíte rode offline e determinística.

A segunda preocupação é **SSRF**: geocoding e Receita buscam URLs/hosts que, se mal restritos, viram vetor de SSRF (A10). Como minhareceita.org pode ser self-hosted e o geocoding pode ser um Nominatim configurável, os adapters DEVEM validar host contra allowlist e rejeitar IPs privados/link-local antes de conectar e após redirect.

**Primary recommendation:** Reusar a base de segurança da Phase 2 verbatim (anti-enumeração, aware UTC, PII-scrub, RFC-7807). Implementar cada integração externa como `Protocol` + impl `httpx` + `StubAdapter`, selecionado por `settings.environment`. Validar CPF/CNPJ server-side com `validate-docbr` (não hand-roll o dígito verificador). Modelar o merchant como máquina de estados explícita (4 estados) com transições logadas no `audit_log` existente. Seeds idempotentes via `seed.py` (upsert por chave natural), planos como dados editáveis (DRV-009). OTP e janelas de retry em aware UTC (TD-010).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Validação de CPF/CNPJ (dígito + formato) | API / Backend | Frontend (UX imediata) | Server é autoridade (A04); front é só conveniência — nunca confiar no client |
| Anti-duplicidade + anti-enumeração (RN-011) | API / Backend | — | Decisão de existência de conta jamais no client; resposta em tempo ~constante no server |
| Validação de CNPJ na Receita | API / Backend (via adapter) | — | SSRF e segredos exigem que a chamada saia do server, nunca do browser |
| OTP de SMS (geração, expiração, tentativas) | API / Backend | SMS provider (entrega) | Estado do OTP é server-side; provider só transporta |
| Geocoding → vínculo de área | API / Backend (via adapter) | — | Decisão de elegibilidade de área é invariante de negócio (server) |
| Máquina de estados do merchant | API / Backend | — | Transições e audit append-only são server-only (RN-012) |
| Job de revalidação Receita (retry) | Worker (arq) | — | Trabalho assíncrono fora do request; janelas em aware UTC |
| Seeds (área Pádua, planos, admin) | Backend (script CLI) | — | Bootstrap idempotente; nunca via UI |
| Wizard / stepper / progresso parcial | Frontend Server (SSR Angular) | Browser (estado do stepper) | UX de multi-step; persistência de rascunho é discricionária (D-01/discretion) |
| Aviso persistente `pending_payment` | Frontend | API (fonte do status) | Render do banner é UI; status canônico vem do backend |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115.* | API REST `/v1` | Já é o stack (Phase 1/2) [VERIFIED: apps/api/pyproject.toml] |
| SQLAlchemy | >=2,<3 | ORM, parametrização (A03) | Já no stack; SQL parametrizado por padrão [VERIFIED: pyproject.toml] |
| Alembic | >=1.13,<2 | Migrations das novas entidades | Já no stack [VERIFIED: pyproject.toml] |
| Pydantic | >=2.7,<3 | Validação de entrada (A03), `extra="forbid"` | Já no stack [VERIFIED: pyproject.toml] |
| httpx | >=0.27,<1 | Cliente async dos adapters (Receita/SMS/SES/geocoding) | Já presente (dev dep); **mover para runtime dep** [VERIFIED: pyproject.toml — atualmente só em `[dependency-groups].dev`] |
| arq | >=0.26,<0.27 | Worker do job de revalidação Receita (retry 6/6/12/24h) | Já boota (`workers/settings.py`, `workers/tasks.py`) [VERIFIED: pyproject.toml + apps/api/app/workers/] |
| argon2-cffi | >=25,<26 | Hash de senha do merchant_user | Já usado no `auth/` (Phase 2) [VERIFIED: pyproject.toml] |
| pyotp | >=2.9,<3 | Já no stack p/ TOTP; **avaliar** para OTP de SMS ou OTP custom | Presente; OTP de SMS pode ser HOTP/custom — ver Don't Hand-Roll [VERIFIED: pyproject.toml] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| validate-docbr | 2.0.0 | Validação de dígito verificador de CPF/CNPJ server-side | SEMPRE no backend; não hand-roll o algoritmo [VERIFIED: pip index versions validate-docbr → 2.0.0] |
| brutils | 2.4.0 | Alternativa (valida + formata CPF/CNPJ/CEP/telefone) | Se quiser formatação BR além de validação [VERIFIED: pip index versions brutils → 2.4.0] |

**Recomendação:** `validate-docbr` para validação pura; se a phase também precisar de **formatação/normalização** (CEP, telefone E.164), `brutils` cobre mais casos. Escolher UMA para evitar redundância. `[ASSUMED]` que `validate-docbr` é suficiente para o escopo desta phase (só validação, não formatação rica).

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| validate-docbr | hand-roll do dígito verificador | NÃO fazer — algoritmo tem casos de borda (CPFs repetidos `111.111.111-11`, máscara, CNPJ alfanumérico 2026) que biblioteca testada já cobre |
| Nominatim/OSM (geocoding) | Google Geocoding API | Nominatim é grátis/self-hostável (alinha com OSRM/MapLibre do projeto, integracoes.md §8) mas tem rate limit de uso público; Google é pago e exige chave/segredo |
| OTP custom (HOTP) | pyotp TOTP | TOTP é time-based (30s) — ruim p/ SMS (latência); OTP de SMS quer código numérico curto com expiração própria (5–10min) e contador de tentativas server-side |

**Installation (deltas sobre o que já existe):**
```bash
# apps/api — adicionar como RUNTIME deps:
uv add httpx          # já existe como dev; promover p/ runtime (adapters usam em produção)
uv add validate-docbr # ou: uv add brutils
```

**Version verification (executado nesta sessão):**
- `validate-docbr` → **2.0.0** [VERIFIED: pip index versions, 2026-06-10]
- `brutils` → **2.4.0** [VERIFIED: pip index versions, 2026-06-10]
- `httpx`, `arq`, `argon2-cffi`, `pydantic`, `sqlalchemy` → versões pinadas já no `pyproject.toml` [VERIFIED: leitura do arquivo]

## Architecture Patterns

### System Architecture Diagram

```
[Browser: Wizard Angular]
   │  POST /v1/merchants/signup  (CNPJ/CPF, nome, categoria, telefone E.164, email, senha)
   ▼
[FastAPI /v1] ── Pydantic (extra="forbid", EmailStr, validador CPF/CNPJ) ──┐
   │                                                                        │ falha → 422 RFC-7807
   ▼                                                                        │
[MerchantService]                                                          │
   │  1. valida dígito CPF/CNPJ (validate-docbr) ─── inválido → 422        │
   │  2. checa unicidade CNPJ/CPF+tel+email (RN-011) ── colisão →          │
   │        resposta anti-enumeração em tempo ~constante (200 genérico)    │
   │  3. cria User+merchant_user (argon2id) + merchant(status=pending_*)   │
   │                                                                        │
   ├──► [ReceitaAdapter (Protocol)]                                        │
   │        ├─ Real: httpx → minhareceita.org (allowlist host, no IP priv) │
   │        │         fallback → BrasilAPI                                  │
   │        └─ Stub: retorna situação fixa (dev/test, sem rede)            │
   │        ├─ ativa  → segue                                              │
   │        ├─ inativa→ E1: bloqueia + msg suporte                         │
   │        └─ down   → E4: status=pending_validation, enfileira job       │
   │                                                                        │
   ├──► [SmsOtpAdapter] gera OTP (aware UTC exp, tentativas) → Zenvia/Twilio (stub em test)
   ├──► [EmailAdapter (SES)] link de confirmação (token) (stub em test)    │
   │                                                                        │
   ├──► [GeocodingAdapter] endereço → (lat,lng) → resolve área (POINT-in-area)
   │        ├─ área encontrada → vincula area_id                           │
   │        └─ sem área → "Ainda não chegamos aí" + captura de interesse   │
   │                                                                        │
   ├──► [PlanService] Free → cria merchant_subscriptions(active)           │
   │                  Pago → merchant fica pending_payment (sem checkout)   │
   │                                                                        │
   └──► [audit_log] cada transição de status (RN-012, append-only)         │
                                                                            │
[arq worker] ── job revalidate_receita (retry 6/6/12/24h, aware UTC) ──────┘
                 pending_validation → ativa | esgota retries → escala admin área
```

### Recommended Project Structure
```
apps/api/app/
├── merchants/
│   ├── models.py          # Merchant (AreaScopedMixin), MerchantUser, MerchantSubscription
│   ├── schemas.py         # SignupBody (extra="forbid"), validadores CPF/CNPJ/E.164
│   ├── service.py         # MerchantService: máquina de estados, anti-enumeração
│   ├── state_machine.py   # transições válidas pending_*→active→suspended
│   ├── router.py          # /v1/merchants/* (signup, confirm-email, confirm-phone)
│   └── otp.py             # geração/validação OTP (aware UTC, tentativas)
├── plans/
│   ├── models.py          # SubscriptionPlan (Free imutável seed)
│   └── service.py
├── integrations/
│   ├── base.py            # Protocols: ReceitaPort, SmsPort, EmailPort, GeocodingPort
│   ├── http.py            # cliente httpx compartilhado + guarda SSRF (allowlist + IP check)
│   ├── receita.py         # ReceitaHttpAdapter (minhareceita + BrasilAPI fallback)
│   ├── receita_stub.py    # ReceitaStubAdapter (dev/test)
│   ├── sms.py / sms_stub.py
│   ├── email.py / email_stub.py
│   ├── geocoding.py / geocoding_stub.py
│   └── factory.py         # seleciona real vs stub por settings.environment
├── workers/tasks.py        # + revalidate_receita (job)
└── ...
tools/
└── seed.py                # idempotente: área Pádua + 4 planos + admin bootstrap (D-09)
```

### Pattern 1: Adapter (Protocol) + impl real + stub
**What:** Cada integração externa é um `typing.Protocol`; uma impl `httpx` para produção e uma `Stub` para dev/teste. A factory escolhe por `settings.environment`.
**When to use:** Toda chamada de rede a serviço externo (Receita, SMS, SES, geocoding).
**Example:**
```python
# integrations/base.py
from typing import Protocol
from dataclasses import dataclass

@dataclass(frozen=True)
class ReceitaResult:
    situacao: str          # "ativa" | "inativa" | "inexistente"
    razao_social: str | None
    cnaes: list[str]

class ReceitaPort(Protocol):
    async def consultar_cnpj(self, cnpj: str) -> ReceitaResult | None: ...
    # None == provedor indisponível (E4 → pending_validation)

# integrations/receita_stub.py — usado em dev/test, NUNCA chama rede
class ReceitaStubAdapter:
    def __init__(self, scenario: str = "ativa") -> None:
        self._scenario = scenario
    async def consultar_cnpj(self, cnpj: str) -> ReceitaResult | None:
        if self._scenario == "down":
            return None
        return ReceitaResult(situacao=self._scenario, razao_social="STUB LTDA", cnaes=[])
```
[CITED: padrão Protocol/adapter — owasp-security A10 + DRV-006 (CONTEXT.md D-03)]

### Pattern 2: Máquina de estados explícita do merchant
**What:** Transições válidas declaradas; transição inválida levanta erro; toda transição registra no `audit_log` (RN-012).
**When to use:** Mudança de `status` do merchant.
**Example:**
```python
# merchants/state_machine.py
MERCHANT_TRANSITIONS = {
    "pending_payment":    {"active", "suspended"},
    "pending_validation": {"active", "suspended"},
    "active":             {"suspended"},
    "suspended":          {"active"},
}
def assert_transition(current: str, target: str) -> None:
    if target not in MERCHANT_TRANSITIONS.get(current, set()):
        raise InvalidTransitionError(current, target)  # RFC-7807 422
```
[ASSUMED] conjunto de transições — derivado de D-05; confirmar com produto se `suspended→pending_*` existe.

### Pattern 3: OTP de SMS com aware UTC (TD-010)
**What:** OTP numérico curto, expiração e contador de tentativas server-side, comparação constante.
**Example:**
```python
# merchants/otp.py
from datetime import UTC, datetime, timedelta
import secrets
from app.db.mixins import ensure_aware_utc

OTP_TTL = timedelta(minutes=10)
OTP_MAX_ATTEMPTS = 5

def new_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"

def is_expired(created_at: datetime) -> bool:
    return datetime.now(UTC) - ensure_aware_utc(created_at) > OTP_TTL  # aware UTC, TD-010
```
[CITED: reuso do padrão aware UTC de `apps/api/app/db/mixins.py` (TD-010 já resolvido)]

### Anti-Patterns to Avoid
- **Hand-roll do dígito verificador de CPF/CNPJ:** casos de borda (sequências repetidas, máscara, CNPJ alfanumérico que entra em vigor jul/2026) — usar `validate-docbr`/`brutils`.
- **Adapter que chama rede no teste:** quebra determinismo e o Gate 5; sempre `Stub` em `environment in {dev,test}`.
- **Revelar QUAL dado colidiu (RN-011/E2):** mensagem única "Já existe conta com esse dado".
- **OTP com `==`:** usar `secrets.compare_digest`.
- **Geocoding/Receita buscando URL do usuário sem allowlist:** SSRF (A10).
- **CPF/CNPJ em log ou em URL:** A09 FAIL-BLOCK + LGPD anti-pattern.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Validação dígito CPF/CNPJ | algoritmo próprio | `validate-docbr` 2.0.0 / `brutils` 2.4.0 | Casos de borda + CNPJ alfanumérico jul/2026; biblioteca testada |
| Cliente HTTP async + retry/timeout | wrapper próprio sobre urllib | `httpx` (já no stack) | Timeout, redirects, async nativo |
| Hash de senha | qualquer coisa | `argon2-cffi` (já em `auth/`) | A02 — reusar Phase 2 |
| Aware UTC / timestamps | `datetime.utcnow()` | `db/mixins.py` (`_utcnow`, `ensure_aware_utc`) | TD-010 já resolvido; não reintroduzir naive |
| Anti-enumeração / tempo constante | nova lógica | padrão de `auth/service.py` (verify_dummy) | Phase 2 já entrega; reusar verbatim |
| PII scrub em log | filtro ad-hoc por log | denylist central (`config.json > observability.pii_fields_forbidden_in_logs`) + `core/logging.py` | A09 — redação estrutural, não disciplina |
| Job scheduler/retry | cron caseiro | arq (já boota) | `workers/` já pronto p/ enfileirar |
| Erros HTTP | dicts soltos | `core/exceptions.py` (RFC-7807) | Padrão estabelecido (Phase 2) |

**Key insight:** ~70% do que esta phase precisaria "construir" já existe na Phase 2 (auth, aware UTC, PII-scrub, RFC-7807, AreaScoped, worker). O risco real está concentrado nos 4 adapters externos — aí o esforço deve ir para contratos + stubs + guardas SSRF, não para a base.

## Runtime State Inventory

> Phase greenfield (adiciona entidades novas; não renomeia/migra estado existente). Seção mantida apenas para registrar estado que os SEEDS criam.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Nenhum dado pré-existente a migrar — entidades `merchants`/`merchant_users`/`subscription_plans`/`merchant_subscriptions` são novas. | Migrations Alembic novas |
| Live service config | Adapters reais (Receita/SMS/SES/geocoding) precisam de hosts/credenciais em env (não commitados). | `.env.example` com placeholders; segredos via env |
| OS-registered state | Nenhum — None (verificado: sem Task Scheduler/systemd nesta phase). | None |
| Secrets/env vars | Novos: `RECEITA_BASE_URL`, `RECEITA_ALLOWLIST_HOSTS`, `ZENVIA_TOKEN`, `TWILIO_*`, `SES_*`, `GEOCODING_BASE_URL`. Todos só em env. | `.env.example`; nunca no repo (A02/Segredos) |
| Build artifacts | Nenhum — None. | None |

## Common Pitfalls

### Pitfall 1: Adapter real vazando para a suíte de testes
**What goes wrong:** Teste chama Receita/SMS real → flaky, lento, custo, e o Gate 5 valida contra serviço vivo (não contra contrato).
**Why it happens:** Factory não desacoplada de `settings.environment`.
**How to avoid:** `factory.py` retorna `Stub*` quando `environment in {dev,test}`; teste injeta cenário (`ReceitaStubAdapter("down")` para E4).
**Warning signs:** Teste que precisa de rede; tempo de suíte sobe; falha intermitente.

### Pitfall 2: Janela de retry / OTP com datetime naive
**What goes wrong:** Comparação naive×aware levanta `TypeError` ou calcula janela errada → OTP nunca expira ou job dispara fora de hora.
**Why it happens:** `datetime.utcnow()` em vez do helper do projeto (TD-010).
**How to avoid:** Sempre `datetime.now(UTC)` + `ensure_aware_utc` em valores lidos do banco.
**Warning signs:** `can't compare offset-naive and offset-aware datetimes` nos testes.

### Pitfall 3: Mensagem de colisão vazando o dado
**What goes wrong:** "E-mail já cadastrado" vs "CNPJ já cadastrado" permite enumerar quais CNPJs/e-mails têm conta (antifraude — F-01 E2).
**Why it happens:** Mensagem específica por campo.
**How to avoid:** Mensagem única; resposta em tempo ~constante (mesmo padrão `verify_dummy` do auth).
**Warning signs:** Branches de erro distintos por campo no service.

### Pitfall 4: Seed não-idempotente
**What goes wrong:** Rodar `seed.py` duas vezes duplica planos/área ou falha por UNIQUE.
**Why it happens:** INSERT cego.
**How to avoid:** Upsert por chave natural (plano por `code`, área por `codename`, admin por `email`); `seed.py` checa existência antes.
**Warning signs:** Erro de constraint na 2ª execução; CI que recria DB falha.

### Pitfall 5: CNPJ alfanumérico (jul/2026)
**What goes wrong:** Validação assume CNPJ só numérico; a partir de jul/2026 a Receita emite CNPJ alfanumérico → cadastros legítimos rejeitados.
**Why it happens:** Regex/algoritmo legado.
**How to avoid:** Usar versão atual de `validate-docbr`/`brutils` (suporte ao formato novo) e não regex caseira.
**Warning signs:** Falha de validação em CNPJs recém-emitidos. [ASSUMED — confirmar suporte da lib à versão instalada]

## Code Examples

### Guarda SSRF no cliente HTTP dos adapters (A10)
```python
# integrations/http.py
import ipaddress, socket
from urllib.parse import urlparse

ALLOWLIST_HOSTS = set()  # carregado de settings (Receita, geocoding, SES, SMS)

def assert_safe_url(url: str) -> None:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host not in ALLOWLIST_HOSTS:
        raise SsrfBlockedError(host)                      # A10: allowlist de host
    for info in socket.getaddrinfo(host, parsed.port or 443):
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_link_local or ip.is_loopback:
            raise SsrfBlockedError(host)                  # rejeita 10.x/192.168/169.254/::1
# revalidar após redirect; httpx: follow_redirects=False e checar Location manualmente
```
[CITED: owasp-security A10 — "Resolver DNS e rejeitar IPs privados/link-local antes de conectar; revalidar pós-redirect"]

### Validação de CPF/CNPJ no schema (A03 — entrada estreita)
```python
# merchants/schemas.py
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from validate_docbr import CPF, CNPJ

class MerchantSignupBody(BaseModel):
    model_config = ConfigDict(extra="forbid")   # A03: previne mass assignment
    account_type: Literal["cnpj", "cpf"]
    document: str
    trade_name: str
    category: str
    phone_e164: str
    email: EmailStr
    password: str

    @field_validator("document")
    @classmethod
    def _valid_doc(cls, v: str, info) -> str:
        digits = "".join(c for c in v if c.isalnum())
        ok = (CNPJ().validate(digits) if info.data.get("account_type") == "cnpj"
              else CPF().validate(digits))
        if not ok:
            raise ValueError("documento_invalido")
        return digits
```
[CITED: validate-docbr 2.0.0 API; owasp-security A03 "Pydantic v2 com tipos estreitos + extra='forbid'"]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CNPJ numérico (14 dígitos) | CNPJ alfanumérico | jul/2026 (Receita Federal) | Validação deve aceitar alfanumérico — usar lib atualizada [CITED: cronograma público da Receita; ASSUMED quanto ao suporte exato da lib] |
| `datetime.utcnow()` (naive) | `datetime.now(UTC)` aware | Python 3.12+ deprecou utcnow() | Já resolvido no projeto (TD-010, `db/mixins.py`) |

**Deprecated/outdated:**
- `datetime.utcnow()`: deprecado; o projeto já não usa (helper aware UTC em `db/mixins.py`).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | minhareceita.org self-hosted é primário e o contrato de resposta (campos `situacao`/`cnaes`/`razao_social`) tem essa forma | Stack / Adapter Receita | Adapter precisa remapear campos; contrato do Gate 5 muda |
| A2 | BrasilAPI `/cnpj/v1/{cnpj}` é o endpoint de fallback e retorna situação cadastral | Adapter Receita | Fallback não funcional → mais cadastros em pending_validation |
| A3 | Geocoding será Nominatim/OSM self-host (discretion) com endpoint `/search` | Geocoding | Provider diferente muda parsing e quota |
| A4 | OTP de SMS é código numérico 6 dígitos, TTL 10min, 5 tentativas | OTP | Política de produto pode diferir |
| A5 | Webhook/callback de status de SMS (Zenvia/Twilio) não é obrigatório nesta phase (OTP é síncrono do ponto de vista do fluxo) | SMS | Se status assíncrono for exigido, adicionar endpoint de callback |
| A6 | Valores dos planos (Início/Profissional/Sem Limite) são placeholders editáveis (DRV-009), Free=R$0/2 entregas/taxa R$2 | Seeds | Apenas dados de seed; baixo risco (editável) |
| A7 | `validate-docbr` 2.0.0 suporta CNPJ alfanumérico (jul/2026) | State of the Art / validação | CNPJs novos rejeitados — testar antes; se não, trocar lib/versão |
| A8 | Transições do merchant incluem `suspended↔active` mas não `active→pending_*` | State machine | Transição faltante levanta erro indevido |

## Open Questions

1. **Contrato real da API de Receita (minhareceita self-host + BrasilAPI)**
   - What we know: providers definidos (DRV-006); falha → pending_validation.
   - What's unclear: forma exata do JSON de resposta de cada provider.
   - Recommendation: **Task de spike** — capturar 1 resposta real de cada provider, fixar como fixture do stub. (Regra 12 → vira task, não "verifique depois".)

2. **Geocoding provider exato + quota**
   - What we know: discretion permite Nominatim/OSM.
   - What's unclear: self-host vs público (rate limit), endpoint, parsing.
   - Recommendation: **Task** decidir provider + fixar contrato no stub; se público, documentar rate limit como TD.

3. **Callback de status de SMS**
   - What we know: integracoes.md §4 menciona "status por callback".
   - What's unclear: se a confirmação de OTP desta phase depende de callback assíncrono ou é puramente "usuário digita o código".
   - Recommendation: **Decisão consciente** — assumir OTP síncrono (usuário digita); registrar TD se callback de delivery-status for necessário em phase futura.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | API | ✓ (pinned) | ==3.13.* | — |
| httpx | Adapters | ✓ (dev dep — promover a runtime) | >=0.27,<1 | — |
| arq + Redis | Job de revalidação | ✓ | arq 0.26 / redis 5 | — |
| validate-docbr | Validação CPF/CNPJ | ✗ (a instalar) | 2.0.0 | brutils 2.4.0 |
| Receita API (minhareceita/BrasilAPI) | Validação CNPJ | runtime externo | — | StubAdapter em dev/test; pending_validation em prod (E4) |
| SMS (Zenvia/Twilio) | OTP | runtime externo | — | Stub em dev/test; degrade e-mail+push (integracoes.md §4) |
| AWS SES | Confirmação e-mail | runtime externo | — | Stub em dev/test; fila com retry |
| Geocoding (Nominatim/OSM) | Vínculo de área | runtime externo | — | Stub em dev/test |

**Missing dependencies with no fallback:** Nenhuma bloqueante — todos os externos têm Stub para dev/test e degrade seguro em prod.
**Missing dependencies with fallback:** `validate-docbr` (instalar; fallback `brutils`).

## Validation Architecture

> nyquist_validation não está explicitamente `false` em config.json → seção incluída.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.2 + pytest-asyncio + aiosqlite (suíte offline) |
| Config file | `apps/api/pyproject.toml` ([tool.pytest...] / [dependency-groups].dev) |
| Quick run command | `cd apps/api && uv run pytest -x -q` |
| Full suite command | `cd apps/api && uv run pytest && uv run ruff check .` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-008 (E1) | CNPJ inativo → bloqueio + msg | unit | `uv run pytest tests/merchants/test_signup.py::test_cnpj_inativo_bloqueia -x` | ❌ Wave 0 |
| REQ-008 (E2) | Colisão → msg anti-enumeração, tempo ~constante | unit | `uv run pytest tests/merchants/test_signup.py::test_colisao_anti_enumeracao -x` | ❌ Wave 0 |
| REQ-008 (E3) | Plano pago falha → pending_payment + Free usável | unit | `uv run pytest tests/merchants/test_signup.py::test_pagamento_falha_vira_free -x` | ❌ Wave 0 |
| REQ-008 (E4) | Receita down → pending_validation + job enfileirado | unit | `uv run pytest tests/merchants/test_signup.py::test_receita_down_pending_validation -x` | ❌ Wave 0 |
| REQ-008 (job) | Retry 6/6/12/24h em aware UTC | unit | `uv run pytest tests/workers/test_revalidate_receita.py -x` | ❌ Wave 0 |
| REQ-009 | Seeds idempotentes (rodar 2x não duplica) | integration | `uv run pytest tests/tools/test_seed_idempotent.py -x` | ❌ Wave 0 |
| REQ-006 | UNIQUE por tipo de conta + resposta genérica | unit | `uv run pytest tests/merchants/test_uniqueness.py -x` | ❌ Wave 0 |
| (SSRF) | Adapter rejeita host fora da allowlist / IP privado | unit | `uv run pytest tests/integrations/test_ssrf_guard.py -x` | ❌ Wave 0 |
| (OTP) | OTP expira (aware UTC) + lockout de tentativas | unit | `uv run pytest tests/merchants/test_otp.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd apps/api && uv run pytest -x -q`
- **Per wave merge:** `cd apps/api && uv run pytest && uv run ruff check .`
- **Phase gate:** suíte completa verde + Gate 5 (integration-checker com stubs) antes de `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tests/integrations/conftest.py` — fixtures de Stub adapters (cenários ativa/inativa/down)
- [ ] `tests/merchants/test_signup.py` — REQ-008 E1–E4
- [ ] `tests/merchants/test_uniqueness.py` — REQ-006
- [ ] `tests/merchants/test_otp.py` — OTP aware UTC + tentativas
- [ ] `tests/integrations/test_ssrf_guard.py` — A10
- [ ] `tests/workers/test_revalidate_receita.py` — job retry aware UTC
- [ ] `tests/tools/test_seed_idempotent.py` — REQ-009

## Security Baseline

> Gate 4 obrigatório — phase coleta PII (CNPJ/CPF/telefone/e-mail) e tem `has_pii: true` + `has_external_integration: true`. Fonte: `.claude/skills/owasp-security/SKILL.md`. Threat model curto (A04): quem abusa, o que ganha, pior caso.

### Threat Model — ameaças e mitigações

| # | Ameaça | STRIDE | Mitigação | Fonte owasp-security |
|---|--------|--------|-----------|----------------------|
| T1 | **Enumeração de conta** no cadastro (atacante descobre quais CNPJs/e-mails/telefones têm conta variando o input e lendo a resposta) | Information Disclosure | Mensagem única "Já existe conta com esse dado" (RN-011/E2); resposta em **tempo ~constante** (reusar `verify_dummy` de `auth/service.py`); nunca branch de erro por campo | A05 ("nunca 'usuário não existe'"); A01 |
| T2 | **SSRF via geocoding** (atacante põe endereço/host que faz o server buscar IP interno/metadata 169.254.169.254) | Tampering / Info Disclosure | Allowlist de host no adapter + rejeitar IP privado/link-local/loopback antes de conectar e **após redirect**; timeout curto; sem credenciais ambiente | A10 (texto integral citado em Code Examples) |
| T3 | **SSRF via adapter Receita** (minhareceita self-host → `RECEITA_BASE_URL` configurável vira vetor se apontar p/ interno) | Tampering | `RECEITA_BASE_URL` e BrasilAPI em **allowlist fixa**; mesma guarda `assert_safe_url`; `follow_redirects=False` | A10 |
| T4 | **Injeção (SQL/mass assignment)** via campos do cadastro | Tampering | SQLAlchemy parametrizado (A03); Pydantic v2 com tipos estreitos (`EmailStr`, `Literal`), `extra="forbid"` em todos os schemas de escrita | A03 |
| T5 | **Abuso de OTP de SMS** (brute force do código; reenvio em massa p/ esgotar quota/custo) | Spoofing / DoS | OTP 6 dígitos com **expiração** (TTL 10min, aware UTC); **máx tentativas** (5) com lockout; rate limit de reenvio por conta+IP; `secrets.compare_digest` na verificação | A04 (rate limit nas duas dimensões), A07 (lockout progressivo) |
| T6 | **PII em log** (CNPJ/CPF/telefone/e-mail aparecendo em log) | Information Disclosure | Denylist central já em `config.json > observability.pii_fields_forbidden_in_logs` + `core/logging.py`; **adicionar `cpf`/`cnpj`/`phone`** à denylist; em log, só hint mascarado (`jo***@gmail.com`); CPF/CNPJ nunca em URL | A09 (FAIL-BLOCK), LGPD §Logs sem PII |
| T7 | **Spam/abuso de cadastro** (criação massiva de lojas falsas, custo de SMS/Receita) | DoS | Rate limit **por IP** no endpoint de signup (derivar: ~5/min por IP — endpoint caro chama Receita+SMS); CAPTCHA opcional como TD; validação Receita antes de ativar | A04 (endpoints caros → orçamento de custo) |
| T8 | **Input BR malformado** (CPF/CNPJ com dígito inválido aceito) | Tampering | Validação de dígito verificador server-side com `validate-docbr` (não confiar no front); normalização para dígitos antes de persistir/checar unicidade | A03 (validação de entrada), A04 (server é autoridade) |
| T9 | **Violação LGPD** (coleta sem base legal, consentimento ausente, sem minimização) | Compliance | Consent granular não pré-marcado (Termos+Privacidade) no signup; base legal = execução de contrato (CNPJ/dados da loja) + consentimento (comunicações); minimização (só o necessário para F-01); link p/ política de privacidade visível (RN-021) | LGPD §Coleta, §Consent, §Checklist PLAN |
| T10 | **Resiliência insegura** (Receita/SMS fora → bloqueia tudo OU libera sem controle) | Availability / Tampering | **Degrade seguro**: Receita down → `pending_validation` + Free com limite + job retry (não bloqueia, não ativa cegamente); SMS down → fallback Zenvia→Twilio→e-mail/push; circuit breaker/timeout em todos os adapters | A04 (insecure design), A10 (timeout) |
| T11 | **Segredo de provider commitado** (token Zenvia/Twilio/SES no repo) | Info Disclosure | Todos os segredos só via env; `.env.example` com placeholders; `.env` no `.gitignore` desde o 1º commit | Gestão de Segredos (FAIL-BLOCK) |
| T12 | **Senha fraca / hash inseguro** do merchant_user | Spoofing | argon2id (reuso `auth/`); política de senha mín. 10–12 chars sem regras arbitrárias (NIST) | A02, A07 |

**Total: 12 ameaças mapeadas.**

### Rate limit — derivação documentada (A04 exige)
- **Signup:** 5/min por IP — endpoint caro (chama Receita + dispara SMS), 5/min inviabiliza criação massiva sem punir usuário legítimo refazendo o form. `[ASSUMED]` — confirmar com produto.
- **Reenvio de OTP:** 3/15min por conta+IP (as duas dimensões, A04) — evita esgotar quota/custo de SMS.
- **Verificação de OTP:** 5 tentativas por OTP, depois invalida e exige novo (A07 lockout).

### LGPD — base legal por campo (minimização)
| Campo | Base legal | Finalidade |
|-------|-----------|-----------|
| CNPJ/CPF | Execução de contrato + obrigação legal (fiscal) | Validar loja (RN-011), nota fiscal futura |
| Nome fantasia, categoria | Execução de contrato | Operação da loja na plataforma |
| Telefone E.164 | Execução de contrato | OTP + notificações operacionais (RN-022 janela) |
| E-mail | Execução de contrato + consentimento (marketing) | Login, confirmação, notificações |
| Senha (hash) | Execução de contrato | Autenticação |
| Endereço/POINT | Execução de contrato | Vínculo de área, despacho |

Consentimento granular (checkbox não pré-marcado) para comunicações opcionais; demais campos sob execução de contrato (não exigem consent, mas exigem informação na política — RN-021).

## Project Constraints (from CLAUDE.md)
- **Regra 7 (Security no researcher):** esta seção `## Security Baseline` é a fonte do threat_model do PLAN.md — herdar daqui.
- **Regra 12 (LOW confidence → task/TD):** itens LOW (contrato Receita, geocoding provider, callback SMS) viram **tasks de spike** ou **TD com urgency_class**, nunca "verifique antes de executar". Ver Open Questions.
- **TD-010 (aware UTC):** OTP expiry, janelas de retry, timestamps — sempre `datetime.now(UTC)` + `ensure_aware_utc`; nunca `utcnow()`.
- **PII fora de log:** CNPJ/CPF/telefone na denylist; mascarar em saídas (CLAUDE.md §75 code_context).
- **`/v1`, RFC-7807, idempotência por header:** padrões já estabelecidos (Phase 2) — reusar.
- **Planos como SEEDS editáveis (DRV-009):** nunca hardcoded.
- **Gate 5 (integration-checker):** valida contratos Receita/SMS/SES/geocoding com **stubs** no teste.

## Sources

### Primary (HIGH confidence)
- `apps/api/app/db/mixins.py` — aware UTC (TD-010), AreaScopedMixin [VERIFIED: leitura]
- `apps/api/app/auth/service.py` — anti-enumeração, tempo constante, lockout [VERIFIED: leitura]
- `apps/api/app/core/logging.py` + `.planning/config.json` — PII denylist [VERIFIED: leitura]
- `apps/api/pyproject.toml` — stack e versões [VERIFIED: leitura]
- `.claude/skills/owasp-security/SKILL.md` — A01/A03/A04/A05/A07/A09/A10, Segredos [CITED]
- `.claude/skills/br/lgpd-compliance/SKILL.md` — base legal, consent, logs sem PII [CITED]
- `pip index versions validate-docbr` → 2.0.0; `brutils` → 2.4.0 [VERIFIED: nesta sessão]
- `projeto/regras-negocio/{fluxos.md F-01, regras.md RN-011/021/028, entidades.md}` [CITED]
- `projeto/docs-externos/integracoes.md §3/§4/§5` [CITED]

### Secondary (MEDIUM confidence)
- CNPJ alfanumérico jul/2026 (cronograma público Receita Federal) [CITED — não verificado contra docs nesta sessão]

### Tertiary (LOW confidence)
- Contrato exato minhareceita.org / BrasilAPI / Nominatim / Zenvia callback [ASSUMED — viram tasks de spike, Regra 12]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versões verificadas no registry e no pyproject existente
- Architecture (adapter, state machine, seeds): HIGH — padrões reusados da Phase 2 + skill owasp
- Security Baseline: HIGH — base já implementada (Phase 2) + skill owasp citada por seção
- Contratos de APIs externas: LOW — viram spikes (Open Questions / Assumptions A1–A5)

**Research date:** 2026-06-10
**Valid until:** 2026-07-10 (estável) — exceção: validação de CNPJ deve ser re-testada após jul/2026 (formato alfanumérico)
