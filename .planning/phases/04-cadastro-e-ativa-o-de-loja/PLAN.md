# PLAN — Phase 4 Plan 01: Cadastro e ativação de loja

> Gerado por `gsd-planner` em 2026-06-10.
> Validado por `gsd-plan-checker` em {date} — status: {PASS|BLOCK|FLAG}.

## Goal

Entregar o fluxo F-01 completo no caminho **Free ativável**: backend (`merchants`, `merchant_users`, `subscription_plans`+seeds, `merchant_subscriptions`, máquina de estados do merchant, adapters Receita/SMS/SES/geocoding com stub de dev/teste, OTP aware-UTC, job de revalidação `arq`, seed idempotente Pádua+4 planos+admin) e frontend (wizard tela 02, seleção de plano tela 16, estados de exceção E1–E4, estado vazio "Ainda não chegamos aí", onboarding). Plano pago → `pending_payment` (sem Safe2Pay real). **SEM** entregador, **SEM** entregas.

## Success criteria

Para fechar este plano, TODOS os critérios abaixo devem ser verdes:

- [ ] **E1** — CNPJ inativo na Receita → cadastro bloqueado com mensagem clara (`test_cnpj_inativo_bloqueia`)
- [ ] **E2** — colisão CNPJ/telefone/e-mail → mensagem anti-enumeração única + resposta em tempo ~constante (`test_colisao_anti_enumeracao`)
- [ ] **E3** — plano pago escolhido → merchant em `pending_payment` usando Free (`test_pagamento_falha_vira_free`)
- [ ] **E4** — Receita fora do ar → `pending_validation` + job de retry enfileirado (`test_receita_down_pending_validation`)
- [ ] Job de revalidação retry 6/6/12/24h em **aware UTC** (`test_revalidate_receita`)
- [ ] **Seed idempotente**: rodar `seed.py` 2x não duplica (área Pádua + 4 planos + admin) (`test_seed_idempotent`)
- [ ] Zero valor de plano hardcoded — todos vêm de `subscription_plans` (SEED, DRV-009)
- [ ] Zero `#hex` hardcoded no frontend — só vars semânticas da Phase 3 (Gate 2)
- [ ] Wireframe-contract de `02-cadastro-loja.html` coberto (stepper, forms BR, E1–E4, estado vazio, planos)
- [ ] Adapter rejeita host fora da allowlist / IP privado (SSRF, `test_ssrf_guard`)
- [ ] `axe-core` zero violações críticas no wizard e na seleção de plano (claro + dark)
- [ ] Todos os testes relacionados passam (`cd apps/api && uv run pytest && uv run ruff check .`)
- [ ] Lint limpo (`make lint`)
- [ ] Commits atômicos por wave com mensagem padronizada

## REQs referenciados

- **REQ-008** — F-01 completo com 4 exceções (E1–E4)
- **REQ-009** — Seeds de planos `[ASSUMIDO]` editáveis (DRV-009)
- **REQ-006** — Anti-duplicidade aplicada (RN-011)

---

## Skills Consultadas

Cada skill abaixo teve regras aplicadas a uma ou mais tasks deste plano. Citar skill sem aplicação concreta é inválido (plan-checker flaga).

- `meta/orchestration-decision-tree` — T-00..T-14: decisão de orquestração — backend (T-01..T-08) e frontend (T-09..T-12) são módulos disjuntos após o contrato de API ser fixado no fim do Wave 2 → **parallel-hint back-front** (ver Execution order). Adapters externos não justificam sub-agente próprio; complexidade está em contratos+stubs, não em paralelismo de IA.
- `domain/mysql-schema-design` — T-01: `merchants`/`merchant_users`/`subscription_plans`/`merchant_subscriptions` com chaves naturais para UNIQUE por tipo de conta (RN-011), FKs para `areas` (Phase 2) e `subscription_plans`, `BIG_ID`, `UTC_DATETIME`, reuso de `AreaScopedMixin`/`TimestampMixin`; índices nos campos de unicidade; Free como seed imutável (flag).
- `domain/fastapi-production-patterns` — T-02 (router thin), T-03 (service), T-05 (adapters httpx async + timeout + circuit/timeout): router parseia contrato e delega ao service; adapters usam `httpx` async com timeout curto e `follow_redirects=False`.
- `product/api-design-contracts` — T-02: `/v1/merchants/*` com RFC-7807, idempotência por header (escrita), `extra="forbid"`, contratos de request/response estáveis consumidos pelo wizard; versionamento `/v1`.
- `owasp-security` — T-03 (anti-enumeração A05/A01, validação A03), T-04 (OTP A04/A07), T-05 (SSRF A10), T-08 (segredos): herda integralmente o `## Security Baseline` do RESEARCH (12 ameaças → mitigações no Threat model).
- `br/lgpd-compliance` — T-03 (minimização: só campos de F-01), T-06 (PII denylist: adicionar `phone` à denylist; mascarar em log), T-11 (consentimento granular não pré-marcado no signup; captura de interesse com base legal de consentimento).
- `quality/observability-production` — T-02/T-08: endpoints logam `request_id`/`status_code`/`duration_ms` SEM PII (CNPJ/CPF/telefone mascarados); transições de status auditadas em `audit_log` (RN-012).
- `domain/mysql-schema-design` + `br/brazilian-forms` — T-01/T-03: CNPJ/CPF normalizados para dígitos antes de persistir; validação dígito verificador server-side com `validate-docbr` (T-13), nunca hand-roll.
- `quality/senior-quality-bar` — T-01..T-14: Gate 8 — sem segredo no repo (T-08 `.env.example`), sem N+1 em listagem de planos, sem injection (Pydantic `extra="forbid"`+SQLAlchemy param), endpoint de signup com decisão de auth explícita (público + rate limit), PII fora de log (T-06).
- **Matriz UI (frontend):**
  - `ui-ux-pro-max` — T-09/T-12: dados em mono (CNPJ, OTP, valores de plano), Fraunces italic em 1 palavra do H1, persimmon como única cor de ação; **anti AI-slop** (sem gradiente/glow/confete).
  - `quality/accessibility-pro` — T-09..T-12: AA nos dois temas, foco visível `--focus-ring`, touch ≥44px, erros via `aria-describedby`, `role`/`aria-live` por estado; stepper não depende só de cor (`aria-current` + check).
  - `product/component-library-governance` — T-09: novos componentes governados `jx-wizard-stepper`/`jx-field`/`jx-plan-card` com story + baseline; reuso dos 4 componentes de estado da Phase 3 (não recriar).
  - `ux-advanced/design-tokens-system` — T-09..T-12: consumir só camada semântica (`var(--surface)`, `var(--brand)`), nunca primitivo nem hex (Gate 2).
  - `ux-advanced/empty-states-polish` — T-11: reuso de `jx-empty-state` para "Ainda não chegamos aí" (causa + ação de captura de interesse).
  - `br/ux-copywriting-ptbr` — T-09..T-12: sentence case, CTA verbo+objeto sem ponto, erro = o que houve + o que fazer; **anti-enumeração** na colisão (mensagem única).
  - `br/brazilian-forms` — T-10: máscara/validação CNPJ/CPF (dígito verificador), telefone BR → E.164, CEP via ViaCEP, `inputmode="numeric"`, **nunca `type="number"`**.
  - `ux-advanced/form-ux-mastery` — T-09/T-10: wizard com stepper, validação inline no blur, persistência de progresso parcial (sessionStorage, nunca senha), um erro por campo via `aria-describedby`, foco gerenciado entre passos.
  - `quality/error-ux-patterns` — T-10/T-11: `jx-error-state` `role="alert"` (E1/E2), `jx-warn-banner` não-bloqueante (pending_*), mensagem acionável.
  - `ux-advanced/onboarding-patterns` — T-12: hint de primeira-entrega no dashboard pós-ativação (progressive disclosure, não modal/tour intrusivo).
  - `ux-advanced/dark-mode-theming` — T-09..T-12: **DEC-001** vale em todo o wizard — tudo consome vars semânticas resolvidas claro/dark da Phase 3; validar contraste AA nos dois temas.
  - `ux-advanced/trust-safety-ux` — T-09/T-10/T-12: sinais de confiança no signup com PII — transparência LGPD inline (por que pedimos CNPJ/CPF/telefone), copy de consentimento de Termos/Privacidade antes do submit, recuperação de acesso sem dark pattern, e mensagem anti-enumeração (RN-011) que protege sem revelar dado. Par obrigatório de `onboarding-patterns` na matriz para auth/signup.

## Skills Dispensadas (com justificativa)

- `domain/saas-billing-canonical` / `domain/safe2pay-escrow-br` — pago é **Phase 10**; nesta phase só o caminho Free e o estado `pending_payment` (aviso). Nenhuma lógica de cobrança/escrow/fatura é implementada (DRV / D-07).
- `ux-advanced/file-upload-ux` — sem upload nesta phase; KYC de entregador (documentos/foto) é **Phase 5**.
- `ux-advanced/data-tables-ux` / `ux-advanced/saas-dashboard-patterns` / `ux-advanced/search-filter-ux` — a tabela de faturas do wireframe 16 é deferida (Phase 10); seleção de plano é grid de cards, não tabela; nenhuma listagem/busca/relatório tabular nesta phase.
- `ux-advanced/gesture-touch-patterns` / `ux-advanced/motion-design-patterns` (avançado) / `product/micro-animations-delight` — `mobile: false`; motion limitado ao slide de passo herdado da Phase 3 (`has_non_trivial_motion: false`); sem gestos.
- `mobile/offline-first` / `mobile/push-notifications-architecture` — `mobile: false`; sem app nativo nesta superfície.
- `ux-advanced/payment-checkout-ux` — checkout real é Phase 10; aqui o card pago só leva a `pending_payment`.
- `ux-advanced/chat-ux-patterns` — sem chat nesta phase.

---

## Tech debt deste plano (verificação obrigatória v0.8+)

| TD ID | Descrição curta | Por que entra (ou não) neste plano | Task que resolve |
|-------|-----------------|-------------------------------------|------------------|
| TD-010 | Naive datetime (aware UTC obrigatório) | `urgency_class: pre_launch_high`, gatilho "toda phase com timestamps" — Phase 4 tem OTP expiry + janelas de retry do job | T-04 (OTP), T-07 (job retry) — usam `datetime.now(UTC)` + `ensure_aware_utc` (`db/mixins.py`); nunca `utcnow()` |
| TD-013 | Taxas sem versionamento temporal | `pre_launch_medium`, "Phase 10 decide" — não é esta phase | — (deferido a Phase 10; planos como seed editável bastam aqui) |
| TD-001/002/003/004/006/007/008/009/011/012 | Diversos | Nenhum tem prazo/gatilho na Phase 4 | — |

Demais TDs: `N/A — sem prazo/gatilho na Phase 4`.

---

## Open questions / LOW confidence do RESEARCH (obrigatório — Regra 12)

Os 4 itens LOW do RESEARCH viram **task explícita** ou **decisão consciente registrada como TD**:

| Item RESEARCH | Confidence | Resolução neste plano |
|---------------|------------|------------------------|
| Contrato real minhareceita.org / BrasilAPI (forma do JSON `situacao`/`cnaes`/`razao_social`) | LOW | **Task T-13 (spike)**: capturar 1 resposta real de cada provider, fixar como **fixture do `ReceitaStubAdapter`**; mapear no adapter real. Critério: fixture commitada + teste verde contra ela |
| Geocoding provider exato + quota (Nominatim/OSM self-host vs público) | LOW | **Task T-13 (decisão + stub)**: decidir provider (default: Nominatim self-host atrás de adapter), fixar contrato `/search` no `GeocodingStubAdapter`. Se público → registrar rate limit como TD-014 |
| Callback de status de SMS (Zenvia/Twilio assíncrono) | LOW | **Decisão consciente**: OTP é **síncrono** (usuário digita o código) nesta phase → **TD-015 registrada** (`urgency_class: post_launch_quarter`): adicionar endpoint de callback de delivery-status se phase futura exigir |
| `validate-docbr` 2.0.0 suporta CNPJ alfanumérico (jul/2026) | LOW | **Task T-13 (teste)**: teste `test_cnpj_alfanumerico` com um CNPJ alfanumérico de exemplo; se a lib instalada falhar → trocar versão/lib (`brutils`) e registrar TD. Critério: teste verde ou troca documentada |

**TDs novas a registrar em `.planning/TECH-DEBT.md` ao executar:**
- **TD-014** (condicional) — geocoding público com rate limit, `post_launch_quarter`, se a decisão de T-13 for provider público.
- **TD-015** — callback de delivery-status de SMS adiado, `post_launch_quarter`, gatilho "phase que exigir confirmação assíncrona de entrega de SMS".

---

## Threat model

Preenchido a partir do `## Security Baseline` do `RESEARCH.md` (12 ameaças). Herdado verbatim — esta é a fonte do threat_model (Regra 7).

| ID | Ameaça | Vetor | Impacto | Likelihood | Mitigação | Task |
|----|--------|-------|---------|------------|-----------|------|
| TH-01 (T1) | Enumeração de conta no cadastro | variar input e ler resposta | Alto | Médio | Mensagem única "Já existe conta com esse dado" (RN-011); resposta tempo ~constante (reuso `verify_dummy` de `auth/service.py`); nunca branch por campo | T-03 |
| TH-02 (T2) | SSRF via geocoding (host/IP interno, 169.254.169.254) | endereço/host malicioso | Alto | Médio | Allowlist de host + rejeitar IP privado/link-local/loopback antes de conectar e após redirect; timeout curto; `follow_redirects=False` | T-05 |
| TH-03 (T3) | SSRF via adapter Receita (`RECEITA_BASE_URL` configurável) | base URL apontando p/ interno | Alto | Baixo | Allowlist fixa (minhareceita + BrasilAPI); mesma guarda `assert_safe_url` | T-05 |
| TH-04 (T4) | Injeção (SQL / mass assignment) | campos do cadastro | Alto | Baixo | SQLAlchemy parametrizado (A03); Pydantic v2 tipos estreitos (`EmailStr`/`Literal`), `extra="forbid"` em todo schema de escrita | T-02, T-03 |
| TH-05 (T5) | Abuso de OTP (brute force / reenvio em massa) | repetir código / reenviar | Médio | Médio | OTP 6 dígitos, TTL 10min (aware UTC), máx 5 tentativas + lockout, rate limit de reenvio por conta+IP, `secrets.compare_digest` | T-04 |
| TH-06 (T6) | PII em log (CNPJ/CPF/telefone/e-mail) | qualquer log | Alto | Médio | Denylist central (`config.json`) — **adicionar `phone`**; mascarar (`jo***@gmail.com`); CPF/CNPJ nunca em URL | T-06 |
| TH-07 (T7) | Spam/abuso de cadastro (lojas falsas, custo SMS/Receita) | criação massiva | Médio | Médio | Rate limit ~5/min por IP no `/v1/merchants/signup` (endpoint caro); validação Receita antes de ativar | T-02, T-08 |
| TH-08 (T8) | Input BR malformado (dígito CPF/CNPJ inválido aceito) | bypass do front | Médio | Médio | Validação dígito verificador server-side com `validate-docbr`; normalizar para dígitos antes de persistir/checar unicidade | T-03, T-13 |
| TH-09 (T9) | Violação LGPD (coleta sem base legal/consent) | signup | Alto | Baixo | Consent granular não pré-marcado (Termos+Privacidade); base legal = execução de contrato + consent (comunicações); minimização (só F-01) | T-03, T-11 |
| TH-10 (T10) | Resiliência insegura (Receita/SMS fora → bloqueia tudo ou libera cego) | indisponibilidade externa | Alto | Médio | Degrade seguro: Receita down → `pending_validation` + Free + job retry; SMS down → Zenvia→Twilio→stub; timeout em todos adapters | T-05, T-07 |
| TH-11 (T11) | Segredo de provider commitado (Zenvia/Twilio/SES token) | repo | Alto | Baixo | Segredos só via env; `.env.example` com placeholders; `.env` no `.gitignore` desde o 1º commit | T-08 |
| TH-12 (T12) | Senha fraca / hash inseguro do merchant_user | signup | Alto | Baixo | argon2id (reuso `auth/`); mín. 10 chars sem regras arbitrárias (NIST) | T-03 |

---

## Performance budget

Herdado de `.planning/config.json > performance_budget`.

**Frontend** (wizard tela 02 + seleção de plano tela 16):
- LCP ≤ 2500ms · INP ≤ 200ms · CLS ≤ 0.1
- Bundle main.js ≤ 400kb gzip · vendor ≤ 800kb gzip
- Lazy loading: rota `loja/cadastro` e `loja/plano` lazy-loaded (standalone components)
- Validação por máscara/ViaCEP não bloqueia paint (assíncrona, com skeleton)

**Backend** (`/v1/merchants/*`):
- p95 ≤ 200ms, p99 ≤ 500ms **no caminho síncrono de resposta** — Receita, SMS, geocoding são chamadas async em job/sub-step, **fora do caminho crítico de p95** (signup retorna pending_* sem aguardar Receita lenta; OTP/link disparados async)
- N+1: zero na listagem de planos (`GET /v1/plans` — single query, planos são poucos)
- Connection pooling reusa o do `db/session.py` (Phase 2)

Medição: Lighthouse CI (frontend); pytest-benchmark nos endpoints críticos.

---

## Observability checklist

Aplicando `quality/observability-production`:

- [ ] `/v1/merchants/signup`, `/confirm-email`, `/confirm-phone`, `/v1/interest` logam `request_id`, `endpoint`, `method`, `status_code`, `duration_ms`
- [ ] **Zero PII**: CNPJ/CPF/telefone/e-mail NUNCA em log — denylist `config.json` + `phone` adicionado (T-06); só hint mascarado
- [ ] Cada transição de status do merchant (`pending_* → active → suspended`) → registro em `audit_log` (RN-012, append-only): ator, motivo, timestamp aware UTC
- [ ] Eventos de cadastro/validação auditados: signup criado, Receita consultada (resultado, sem PII), OTP verificado, área vinculada, plano ativado
- [ ] 4xx → WARNING; 5xx → ERROR; falha de adapter externo → WARNING (degrade esperado, não 5xx)
- [ ] Queries > 100ms logadas com WARNING (threshold do `config.json`)

---

## Error UX checklist

Aplicando `quality/error-ux-patterns` (TEM UI):

- [ ] **E1** — CNPJ inativo → `jx-error-state` `role="alert"`: "CNPJ não está ativo na Receita Federal. Confira o número ou fale com o suporte." + link suporte
- [ ] **E2** — colisão → `jx-error-state` único e idêntico p/ CNPJ/telefone/e-mail: "Já existe uma conta com esse dado. Quer recuperar o acesso?" + "Recuperar acesso" — **sem `aria-invalid` em campo individual** (não vazar qual colidiu)
- [ ] **E3** — `jx-warn-banner` persistente não-dispensável: "Seu pagamento do plano X ainda não foi concluído. Você está usando o Free por enquanto." + "Concluir pagamento"
- [ ] **E4** — `jx-warn-banner` persistente: "Estamos confirmando seu CNPJ na Receita. Sua loja já funciona no plano Free enquanto isso."
- [ ] Validação inline **no blur** (não modal ao submit): CNPJ/CPF/telefone/CEP/senha — mensagem = o que houve + o que fazer ("CNPJ incompleto. Confira os 14 dígitos.")
- [ ] CEP inexistente/ViaCEP fora → `jx-warn-banner` não-bloqueante "Preencha o endereço manualmente" (resiliência, não erro)
- [ ] Toast vs modal vs inline: **inline** (campo) para validação, `jx-error-state` para erro de passo, `jx-warn-banner` para status — consistente

---

## Integration contracts

`integration_check: true` — validado por `gsd-integration-checker` com **stubs** (Gate 5). Os 4 adapters externos têm contrato fixado por stub no teste (nunca chamam rede).

| Contrato | Consumer | Provider | Assertion |
|----------|----------|----------|-----------|
| `POST /v1/merchants/signup` | `apps/web/.../loja/cadastro` (wizard) | `apps/api/app/merchants/router.py` | body: `{account_type, document, trade_name, category, phone_e164, email, password, consent}`; resposta: `{merchant_id, status, next_step}` (status ∈ pending_validation/pending_payment/active) |
| `POST /v1/merchants/{id}/confirm-phone` | wizard passo 2 | `merchants/router.py` | body `{otp}`; resposta `{confirmed: bool}`; OTP server-side aware UTC |
| `GET /v1/plans` | wizard passo 4 + tela 16 | `plans/router.py` | resposta lista `{codename, nome, preco, entregas_mes, taxa_entrega, is_free}` — **valores do SEED**, nunca hardcode |
| `POST /v1/interest` | `jx-empty-state` "Ainda não chegamos" | `merchants/router.py` (ou `interest`) | body `{email, cidade}` + consent; resposta 202 |
| `ReceitaPort.consultar_cnpj` | `MerchantService` | `ReceitaHttpAdapter` / `ReceitaStubAdapter` | retorna `ReceitaResult(situacao, razao_social, cnaes)` \| `None` (None = down → E4); stub: cenários `ativa`/`inativa`/`down` |
| `SmsPort.send_otp` | `MerchantService` | `SmsHttpAdapter` / `SmsStubAdapter` | request `{phone_e164, code}`; stub captura sem rede; fallback Zenvia→Twilio |
| `EmailPort.send_confirm_link` | `MerchantService` | `EmailSesAdapter` / `EmailStubAdapter` | request `{email, token}`; stub captura |
| `GeocodingPort.geocode` | `MerchantService` | `GeocodingHttpAdapter` / `GeocodingStubAdapter` | request `{address}`; resposta `{lat, lng}` \| `None`; resolve área POINT-in-area; stub fixa coordenada Pádua / fora-de-área |

---

## Tasks

### T-00 — Wave 0: scaffolds de teste (Nyquist) + deps

- **Type:** test / infra
- **Files:** `apps/api/tests/integrations/conftest.py`, `apps/api/tests/merchants/test_signup.py`, `test_uniqueness.py`, `test_otp.py`, `apps/api/tests/integrations/test_ssrf_guard.py`, `apps/api/tests/workers/test_revalidate_receita.py`, `apps/api/tests/tools/test_seed_idempotent.py`, `apps/api/pyproject.toml`
- **Skills aplicadas:** `domain/fastapi-production-patterns` — fixtures de stub adapters (cenários ativa/inativa/down) injetáveis; `owasp-security` — testes RED para SSRF e anti-enumeração.
- **Descrição:** Criar arquivos de teste com casos RED (esqueleto + asserts esperados, importando símbolos que ainda não existem). Adicionar deps runtime: `uv add httpx` (promover de dev), `uv add validate-docbr`.
- **Success:** arquivos existem; `uv run pytest` falha por *implementação ausente* (não por import quebrado de teste); deps no `pyproject.toml`.
- **Depends on:** none

### T-01 — Models + migrations Alembic + AreaScoped/Timestamp reuse

- **Type:** migration
- **Files:** `apps/api/app/merchants/models.py`, `apps/api/app/plans/models.py`, `apps/api/alembic/versions/0003_merchants_plans.py`
- **Skills aplicadas:** `domain/mysql-schema-design` — `merchants` (AreaScopedMixin + TimestampMixin, status enum, FK `area_id`→`areas`, lat/lng nullable), `merchant_users` (FK user, FK merchant, role), `subscription_plans` (UNIQUE `code`, `is_free` flag imutável, preco/entregas_mes/taxa como colunas — valores via SEED), `merchant_subscriptions` (FK merchant+plan, status, ciclo); UNIQUE composto por tipo de conta para RN-011 (`document`+`account_type`, `phone_e164`, `email`); índices. Reusa `BIG_ID`/`UTC_DATETIME` de `db/`.
- **Descrição:** Modelar 4 entidades reusando convenções da migration `0002`. `down_revision = "0002_core_auth_multiarea"`, `revision = "0003_merchants_plans"`.
- **Success:** `uv run alembic upgrade head` aplica; `alembic downgrade -1` reverte limpo; UNIQUE constraints presentes.
- **Depends on:** none

### T-02 — Router /v1/merchants + /v1/plans + schemas (contrato de API)

- **Type:** new_endpoint
- **Files:** `apps/api/app/merchants/router.py`, `apps/api/app/merchants/schemas.py`, `apps/api/app/plans/router.py`, `apps/api/app/plans/service.py`, `apps/api/app/api/v1/__init__.py` (registrar routers)
- **Skills aplicadas:** `product/api-design-contracts` — `/v1/merchants/{signup,confirm-email,confirm-phone}`, `/v1/plans`, `/v1/interest`; RFC-7807; idempotência por header em escrita; `extra="forbid"`; rate limit signup ~5/min por IP. `domain/fastapi-production-patterns` — router thin delegando ao service. `owasp-security` A03 — Pydantic tipos estreitos (`EmailStr`, `Literal["cnpj","cpf"]`).
- **Descrição:** Definir o contrato de API estável (consumido pelo frontend). `GET /v1/plans` retorna planos do SEED. **Este é o ponto de fork back-front** (ver Execution order).
- **Success:** `GET /v1/plans` retorna lista do seed; `POST /v1/merchants/signup` valida schema com `extra="forbid"` (422 em campo extra); OpenAPI gerado com os contratos da seção Integration contracts.
- **Depends on:** T-01

### T-03 — MerchantService: máquina de estados + anti-enumeração + validação BR

- **Type:** new_endpoint (lógica de domínio)
- **Files:** `apps/api/app/merchants/service.py`, `apps/api/app/merchants/state_machine.py`
- **Skills aplicadas:** `owasp-security` A05/A01 — unicidade RN-011 com resposta **tempo ~constante** reusando `verify_dummy` de `auth/service.py`; mensagem única anti-enumeração. `br/lgpd-compliance` — minimização + consent obrigatório. `domain/mysql-schema-design`/`br/brazilian-forms` — normalizar documento p/ dígitos via `validate-docbr` antes de checar unicidade. `quality/observability-production` — transições logadas em `audit_log` (RN-012).
- **Descrição:** `assert_transition` (`pending_payment`/`pending_validation`→`active`/`suspended`; `active`→`suspended`; `suspended`→`active`). Cria User+merchant_user (argon2id reuso `auth/`) + merchant. E1/E2/E4 orquestrados aqui.
- **Success:** `test_colisao_anti_enumeracao` verde (mesma mensagem p/ CNPJ/tel/email + tempo ~constante); `test_cnpj_inativo_bloqueia` (E1); transição inválida levanta `InvalidTransitionError` (422 RFC-7807).
- **Depends on:** T-01, T-02

### T-04 — OTP de SMS aware-UTC (TD-010) + confirmação

- **Type:** new_endpoint (lógica)
- **Files:** `apps/api/app/merchants/otp.py`
- **Skills aplicadas:** `owasp-security` A04/A07 — OTP 6 dígitos, TTL 10min, máx 5 tentativas + lockout, rate limit reenvio 3/15min por conta+IP, `secrets.compare_digest`. TD-010 — `datetime.now(UTC)` + `ensure_aware_utc` (`db/mixins.py`), **nunca `utcnow()`**.
- **Descrição:** Geração/validação de OTP server-side. Expiração e tentativas em aware UTC.
- **Success:** `test_otp` verde — OTP expira corretamente (aware UTC), 6ª tentativa invalida e exige novo; comparação constante.
- **Depends on:** T-01

### T-05 — Adapters Receita/SMS/SES/geocoding (Protocol + httpx + Stub + SSRF guard)

- **Type:** infra / integration
- **Files:** `apps/api/app/integrations/base.py`, `http.py`, `receita.py`, `receita_stub.py`, `sms.py`, `sms_stub.py`, `email.py`, `email_stub.py`, `geocoding.py`, `geocoding_stub.py`, `factory.py`
- **Skills aplicadas:** `owasp-security` A10 — `assert_safe_url` (allowlist de host + rejeitar IP privado/link-local/loopback antes de conectar e após redirect, `follow_redirects=False`). `domain/fastapi-production-patterns` — `httpx` async + timeout curto. Pattern adapter (DRV-006/007): `Protocol` + impl real + `Stub`; `factory.py` retorna Stub quando `environment in {dev,test}` (**adapter NUNCA chama rede no teste**).
- **Descrição:** 4 Protocols (`ReceitaPort`/`SmsPort`/`EmailPort`/`GeocodingPort`), impl httpx + stub configurável por cenário. Receita: minhareceita primário + BrasilAPI fallback. SMS: Zenvia→Twilio.
- **Success:** `test_ssrf_guard` verde (rejeita host fora allowlist + IP privado); factory retorna Stub em test; teste não faz rede.
- **Depends on:** none

### T-06 — PII denylist + logging mascarado

- **Type:** infra
- **Files:** `.planning/config.json` (denylist), `apps/api/app/core/logging.py` (mascaramento), `apps/api/app/merchants/service.py` (uso)
- **Skills aplicadas:** `br/lgpd-compliance` + `owasp-security` A09 — adicionar `phone` à `pii_fields_forbidden_in_logs` (já tem `cpf`,`cnpj`,`email`); mascarar em saída (`jo***@gmail.com`); CPF/CNPJ nunca em URL/log.
- **Descrição:** Garantir redação estrutural de PII nos logs de cadastro/validação.
- **Success:** teste/inspeção: log de signup não contém CNPJ/CPF/telefone/e-mail em claro.
- **Depends on:** T-03

### T-07 — Job arq de revalidação Receita (retry 6/6/12/24h aware UTC)

- **Type:** infra (worker)
- **Files:** `apps/api/app/workers/tasks.py` (+ `revalidate_receita`), `apps/api/app/workers/settings.py`
- **Skills aplicadas:** TD-010 — janelas de retry em `datetime.now(UTC)`. `owasp-security` A04 — degrade seguro: esgota retries → escala admin de área. Reuso do worker arq já booteado (Phase 2).
- **Descrição:** Job enfileirado em E4; `pending_validation`→`active` se Receita responder ativa; janelas 6/6/12/24h.
- **Success:** `test_revalidate_receita` verde — retry windows corretas (aware UTC), transição de status ao revalidar.
- **Depends on:** T-03, T-05

### T-08 — Seed idempotente + .env.example + rate limit signup

- **Type:** infra
- **Files:** `apps/api/tools/seed.py`, `apps/api/.env.example`, `apps/api/app/merchants/router.py` (rate limit)
- **Skills aplicadas:** `owasp-security` segredos/A04 — `.env.example` com placeholders (`RECEITA_BASE_URL`, `RECEITA_ALLOWLIST_HOSTS`, `ZENVIA_TOKEN`, `TWILIO_*`, `SES_*`, `GEOCODING_BASE_URL`), nunca segredo no repo; rate limit signup. `quality/senior-quality-bar` Gate 8 — segredos fora do repo. DRV-009 — planos com valores **editáveis no seed**, Free imutável.
- **Descrição:** `seed.py` **idempotente** (upsert por chave natural: plano por `code`, área por `codename` Pádua, admin por `email`). 4 planos com valores `[ASSUMIDO]`. Admin plataforma + admin de área Pádua.
- **Success:** `test_seed_idempotent` verde — rodar 2x não duplica; `.env` no `.gitignore`; valores de plano só no seed.
- **Depends on:** T-01

### T-09 — Frontend: jx-wizard-stepper + jx-field + jx-plan-card (componentes governados)

- **Type:** ui_component
- **Files:** `apps/web/src/app/shared/components/wizard-stepper/*`, `field/*`, `plan-card/*`, `apps/web/src/app/features/loja/cadastro/*.stories.ts`
- **Skills aplicadas:** `product/component-library-governance` — 3 componentes novos com story + baseline. `ux-advanced/design-tokens-system` + `ux-advanced/dark-mode-theming` — só vars semânticas (DEC-001), zero hex. `quality/accessibility-pro` — stepper `aria-current="step"`+check (não só cor), `jx-field` encapsula `aria-describedby`, touch ≥44px. `ui-ux-pro-max` — dados em mono. `ux-advanced/form-ux-mastery` — `jx-field` com máscara + estado de validação.
- **Descrição:** Componentes compartilháveis do wizard. Reusa `jx-empty-state`/`jx-error-state`/`jx-warn-banner`/`jx-loading-skeleton` da Phase 3 (não recria).
- **Success:** stories renderizam em claro+dark; `axe-core` zero violações críticas; grep confirma zero `#hex` nos `.scss`.
- **Depends on:** none (consome só design system Phase 3 — paralelo ao backend)

### T-10 — Frontend: wizard tela 02 (4 passos, forms BR, E1/E2, persistência)

- **Type:** ui_component
- **Files:** `apps/web/src/app/features/loja/cadastro/cadastro.page.*`, `passo-*.component.*`, `apps/web/src/app/features/loja/loja.routes.ts`, `apps/web/src/app/app.routes.ts` (lazy)
- **Skills aplicadas:** `br/brazilian-forms` — máscara/validação CNPJ/CPF (dígito), telefone→E.164, CEP via ViaCEP, `inputmode="numeric"`, nunca `type="number"`. `ux-advanced/form-ux-mastery` — stepper, validação no blur, persistência em sessionStorage (**nunca senha**), foco entre passos. `quality/error-ux-patterns` + `br/ux-copywriting-ptbr` — E1 `jx-error-state`; E2 mensagem única anti-enumeração sem `aria-invalid` por campo. `quality/accessibility-pro` — `aria-live` "Passo N de 4".
- **Descrição:** 4 passos (Identificação → Confirmação e-mail/OTP → Endereço/área → Plano). Consome `/v1/merchants/*`. Rota lazy.
- **Success:** wireframe-contract `02-cadastro-loja.html` coberto; E1/E2 renderizam corretamente; senha nunca em sessionStorage; `axe-core` limpo claro+dark.
- **Depends on:** T-09, **contrato de API de T-02** (consumido, não bloqueante de impl com mock)

### T-11 — Frontend: estado vazio "Ainda não chegamos aí" + captura de interesse + planos (tela 16)

- **Type:** ui_component
- **Files:** `apps/web/src/app/features/loja/cadastro/sem-area.component.*`, `apps/web/src/app/features/loja/plano/plano.page.*`
- **Skills aplicadas:** `ux-advanced/empty-states-polish` — reuso de `jx-empty-state` (causa + ação). `br/lgpd-compliance` — captura de interesse com consentimento. `ui-ux-pro-max` — seleção de plano sem dark pattern ("Continuar no Free" mesmo peso que upgrade), preço em mono, valores do SEED (`jx-plan-card` data-driven). `ux-advanced/design-tokens-system` — zero hex.
- **Descrição:** Estado vazio (endereço fora de área) com `POST /v1/interest`. Seleção de plano: grid de `jx-plan-card` alimentado por `GET /v1/plans` (valores do seed, NUNCA hardcode).
- **Success:** estado vazio renderiza + captura submete; cards exibem valores do `GET /v1/plans` (grep confirma zero valor de plano hardcode no template); sem dark pattern.
- **Depends on:** T-09, contrato T-02

### T-12 — Frontend: estados pending_* (E3/E4) + onboarding pós-ativação

- **Type:** ui_component
- **Files:** `apps/web/src/app/features/loja/dashboard/onboarding-hint.component.*`, integração com `jx-warn-banner`
- **Skills aplicadas:** `quality/error-ux-patterns` — `jx-warn-banner` persistente E3/E4. `ux-advanced/onboarding-patterns` — hint de primeira-entrega (progressive disclosure, não modal/tour). `ui-ux-pro-max` — sem festividade (sem confete/gradiente). `quality/accessibility-pro` — ordem: aviso de status → hint.
- **Descrição:** Banners persistentes pending_payment/pending_validation no dashboard; hint de primeira entrega.
- **Success:** E3/E4 banners renderizam (claro+dark); hint dispensável; coexistência (banner acima do hint); `axe-core` limpo.
- **Depends on:** T-09, contrato T-02

### T-13 — Spike LOW confidence: contratos Receita/geocoding + CNPJ alfanumérico

- **Type:** test / spike
- **Files:** `apps/api/tests/integrations/fixtures/receita_*.json`, `geocoding_*.json`, `apps/api/tests/merchants/test_cnpj_alfanumerico.py`
- **Skills aplicadas:** `owasp-security` — fixtures não contêm PII real. Regra 12 — resolve os 4 LOW do RESEARCH.
- **Descrição:** (a) capturar 1 resposta real minhareceita + BrasilAPI → fixar como fixture do stub; (b) decidir geocoding provider (default Nominatim self-host) + fixar contrato `/search`; (c) decisão consciente OTP síncrono → registrar **TD-015**; (d) teste `test_cnpj_alfanumerico` validando suporte de `validate-docbr` 2.0.0 (se falhar → trocar lib + TD).
- **Success:** fixtures commitadas; `test_cnpj_alfanumerico` verde ou troca documentada; TD-014 (se geocoding público) + TD-015 registradas em `TECH-DEBT.md`.
- **Depends on:** T-05

### T-14 — Testes E1–E4 + seed + integração final (checkpoint)

- **Type:** test
- **Files:** `apps/api/tests/merchants/test_signup.py` (completar), `test_uniqueness.py`, `tests/tools/test_seed_idempotent.py`, `tests/workers/test_revalidate_receita.py`
- **Skills aplicadas:** `owasp-security` — cobertura das 12 ameaças mapeáveis em teste (anti-enumeração, SSRF, OTP lockout). `quality/senior-quality-bar` — sem FAIL-BLOCK aberto.
- **Descrição:** Completar e verdejar todos os testes Wave 0; rodar suíte + ruff; preparar Gate 5 (integration-checker com stubs).
- **Success:** `cd apps/api && uv run pytest && uv run ruff check .` verde; E1–E4 + seed idempotente + SSRF + OTP todos passam.
- **Depends on:** T-03, T-04, T-05, T-06, T-07, T-08

---

## Execution order

Waves (grupos paralelizáveis). **parallel-hint: back-front** — após T-02 fixar o contrato de API (fim do Wave 2 backend), o frontend (T-09..T-12) e o backend restante são **módulos disjuntos** e podem ser executados em paralelo por dois fluxos (`files_modified` de `apps/web/` vs `apps/api/` não se sobrepõem).

- **Wave 0:** T-00 (scaffolds de teste RED + deps)
- **Wave 1 (paralelo):** T-01 (models/migrations), T-05 (adapters+SSRF), T-09 (componentes frontend — só design system Phase 3)
- **Wave 2 (paralelo):** T-02 (contrato API — depende T-01) ‖ T-04 (OTP — depende T-01) ‖ T-13 (spike — depende T-05)
  - **← FORK back-front aqui:** contrato de API fixado em T-02.
- **Wave 3 (paralelo back ‖ front):**
  - **Backend:** T-03 (service — T-01,T-02), depois T-06 (PII — T-03), T-07 (job — T-03,T-05), T-08 (seed — T-01)
  - **Frontend:** T-10 (wizard — T-09 + contrato T-02) ‖ T-11 (estado vazio + planos) ‖ T-12 (pending_* + onboarding)
- **Wave 4:** T-14 (testes E1–E4 + seed + Gate 5 integration-checker) — depende de todo Wave 3 backend

---

## Reconciliation expectations

Ao fim da execução, o `/gsd:reconcile-state 4` verifica:

- Todos os arquivos listados em `files` de cada task existem
- `/v1/merchants/signup`, `/confirm-phone`, `/v1/plans`, `/v1/interest` têm handler implementado
- Skills citadas foram de fato aplicadas: rate limit signup presente, SSRF guard presente, anti-enumeração reusa `verify_dummy`, OTP usa aware UTC, denylist tem `phone`
- Zero valor de plano hardcoded (grep) e zero `#hex` no frontend (grep) — DRV-009 + Gate 2
- Seed idempotente verificável (rodar 2x)
- TD-015 (e TD-014 se aplicável) registradas em `TECH-DEBT.md`
- Nenhum arquivo-fantasma; nenhuma feature fantasma

Divergências entram em `RECONCILIATION.md` antes de fechar a fase.

---

## Rollback plan

- Revert dos commits `feat(phase-4/...)` por wave
- `uv run alembic downgrade -1` para reverter `0003_merchants_plans`
- Remover rotas lazy `loja/cadastro`, `loja/plano` de `app.routes.ts`
- Seed não precisa rollback (idempotente; remoção manual via `code`/`codename` se necessário)
- Adapters reais permanecem desligados em dev/test (factory → Stub) — sem ação de ops

---

## Plan-checker report

{Preenchido automaticamente pelo gsd-plan-checker}

- Status: {PASS | FLAG | BLOCK}
- Skills coverage: {X/Y obrigatórias citadas}
- Threat model: {presente | ausente | incompleto}
- Performance budget: {presente | N/A | incompleto}
- Observability checklist: {presente | N/A | incompleto}
- Integration contracts: {presente | N/A | incompleto}
- Revision iteration: {1 | 2 | 3 | final}
