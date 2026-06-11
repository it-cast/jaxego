---
phase: 10-safe2pay-n-cleo-assinaturas-cobran-a-com-split-escrow-estornos
plan: 01
type: execute
wave: 0
depends_on: [9]
autonomous: false
gap_closure: false
gate: 2
integration_check: true
has_ui: true
has_api: true
has_payments: true
has_pii: true
requirements: [REQ-010, REQ-011, REQ-019, REQ-029, REQ-034, REQ-036]
files_modified:
  # Backend — núcleo (NOVO módulo app/payments/)
  - apps/api/app/payments/__init__.py
  - apps/api/app/payments/crypto.py
  - apps/api/app/payments/port.py
  - apps/api/app/payments/safe2pay_adapter.py
  - apps/api/app/payments/safe2pay_stub.py
  - apps/api/app/payments/factory.py
  - apps/api/app/payments/models.py
  - apps/api/app/payments/schemas.py
  - apps/api/app/payments/service.py
  - apps/api/app/payments/subscriptions.py
  - apps/api/app/payments/escrow.py
  - apps/api/app/payments/reconcile.py
  - apps/api/app/payments/router.py
  - apps/api/app/payments/webhooks_router.py
  - apps/api/app/payments/repo.py
  - apps/api/app/payments/errors.py
  - apps/api/app/payments/fees.py
  # Backend — edits a módulos existentes
  - apps/api/app/core/config.py
  - apps/api/app/merchants/models.py
  - apps/api/app/couriers/service.py
  - apps/api/app/deliveries/service.py
  - apps/api/app/workers/settings.py
  - apps/api/app/workers/tasks.py
  - apps/api/app/main.py
  - apps/api/.env.example
  - apps/api/alembic/versions/0009_safe2pay_billing_escrow.py
  # Tests (Wave 0)
  - apps/api/tests/payments/conftest.py
  - apps/api/tests/payments/test_crypto.py
  - apps/api/tests/payments/test_adapter_haserror.py
  - apps/api/tests/payments/test_split.py
  - apps/api/tests/payments/test_escrow.py
  - apps/api/tests/payments/test_refund.py
  - apps/api/tests/payments/test_webhooks.py
  - apps/api/tests/payments/test_subscription.py
  - apps/api/tests/payments/test_delinquency.py
  - apps/api/tests/payments/test_reconcile.py
  - apps/api/tests/payments/test_plan_change.py
  - apps/api/tests/payments/test_circuit_breaker.py
  # Frontend — checkout/plano/entrega
  - apps/web/src/app/features/plano/plano.page.ts
  - apps/web/src/app/features/plano/components/jx-checkout-method-toggle.component.ts
  - apps/web/src/app/features/plano/components/jx-card-form.component.ts
  - apps/web/src/app/features/plano/components/jx-pix-qr.component.ts
  - apps/web/src/app/features/plano/components/jx-subscription-status.component.ts
  - apps/web/src/app/features/plano/components/jx-plan-compare.component.ts
  - apps/web/src/app/features/plano/components/jx-charge-history.component.ts
  - apps/web/src/app/features/plano/payment-crypto.service.ts
  - apps/web/src/app/features/plano/billing.service.ts
  - apps/web/src/app/features/nova-entrega/nova-entrega.page.ts
  - apps/web/src/app/features/nova-entrega/delivery-payment.service.ts

must_haves:
  truths:
    - "Lojista assina um plano por cartão (RSA-OAEP no cliente) ou PIX automático; assinatura fica active"
    - "Cron diário cobra assinaturas recorrentes; >10d vira blocked, >20d vira cancelado (aware-UTC)"
    - "Lojista cria entrega pagando cartão/PIX; o valor é dividido (split) entre subconta do entregador (corrida) e Jaxegô (taxa + revenue share), com soma EXATA em centavos"
    - "Cartão/PIX recusado na criação → a entrega NÃO nasce (F-03 E3) e o lojista tem retry ou trocar p/ direto"
    - "Corrida cobrada fica em escrow; só entra no saldo do entregador 24h após FINALIZADA sem disputa"
    - "Webhook Safe2Pay duplicado é processado UMA vez (idempotente por IdTransaction+status)"
    - "Subconta do entregador é cadastrada quando o MEI é aprovado (Phase 5); sem MEI não há repasse via plataforma"
    - "Estorno só atinge a própria cobrança (sem IDOR), com valor RN-004; conciliação diária alerta divergência >R$0,01"
    - "API Safe2Pay fora do ar → criação cartão/PIX indisponível, mas pagamento direto segue funcionando (circuit breaker)"
    - "Cartão/CVV/token NUNCA aparecem em texto puro, em log ou no banco; token em repouso é AES-256-GCM; chaves só via env"
  artifacts:
    - path: "apps/api/app/payments/crypto.py"
      provides: "AES-256-GCM (token) + RSA-OAEP-2048 (cartão) — formato base64(nonce12+ct_com_tag)"
      contains: "AESGCM"
    - path: "apps/api/app/payments/port.py"
      provides: "PaymentPort Protocol + dataclasses ChargeResult/Split (centavos inteiros)"
      contains: "class PaymentPort(Protocol)"
    - path: "apps/api/app/payments/safe2pay_adapter.py"
      provides: "impl httpx com _call_safe2pay que SEMPRE checa HasError + assert_safe_url"
      contains: "HasError"
    - path: "apps/api/app/payments/safe2pay_stub.py"
      provides: "Stub determinístico (dev/test, sem rede) — NUNCA chama Safe2Pay real"
      contains: "class PaymentStubAdapter"
    - path: "apps/api/app/payments/models.py"
      provides: "platform_charges, escrow_ledger, payment_webhook_events (UNIQUE idempotência)"
      contains: "platform_charges"
    - path: "apps/api/app/payments/escrow.py"
      provides: "ledger hold/release/freeze; release só FINALIZADA+24h aware-UTC sem disputa"
      contains: "release_escrow"
    - path: "apps/api/app/payments/webhooks_router.py"
      provides: "endpoint público: log → HMAC compare_digest → dedup → enfileira → 200"
      contains: "compare_digest"
    - path: "apps/api/alembic/versions/0009_safe2pay_billing_escrow.py"
      provides: "migration reversível (down_revision 0008_proofs_tracking_notif)"
      contains: "down_revision"
    - path: "apps/web/src/app/features/plano/components/jx-card-form.component.ts"
      provides: "form de cartão que cifra RSA-OAEP no cliente antes de enviar"
      contains: "jx-card-form"
  key_links:
    - from: "apps/web/.../jx-card-form.component.ts"
      to: "GET /v1/payments/chave-publica"
      via: "RSA-OAEP encrypt no cliente"
      pattern: "chave-publica|public.?key"
    - from: "apps/api/app/deliveries/service.py"
      to: "apps/api/app/payments/service.py charge_delivery"
      via: "split na criação de entrega card/pix"
      pattern: "charge_delivery|charge_with_split"
    - from: "apps/api/app/payments/webhooks_router.py"
      to: "payment_webhook_events UNIQUE(transaction_id,status)"
      via: "dedup antes de qualquer efeito financeiro"
      pattern: "already_processed|webhook_events"
    - from: "apps/api/app/workers/settings.py"
      to: "release_escrow / charge_subscriptions_daily / reconcile_safe2pay"
      via: "arq cron_jobs (reusa finalize_deliveries Phase 9)"
      pattern: "cron_jobs|release_escrow"
    - from: "apps/api/app/couriers/service.py (MEI aprovado)"
      to: "PaymentPort.register_subaccount"
      via: "gancho KYC Phase 5 → subconta Safe2Pay"
      pattern: "register_subaccount"

user_setup:
  - service: safe2pay
    why: "PSP de pagamento online (assinatura, cobrança split, escrow, estornos). Implementação roda 100% em Stub no dev/test; produção exige conta real."
    env_vars:
      - name: SAFE2PAY_API_KEY
        source: "Painel Safe2Pay → API → chave de produção/sandbox"
      - name: SAFE2PAY_SANDBOX
        source: "true em staging, false em produção (token recorrente só funciona em produção — Pitfall 5)"
      - name: SAFE2PAY_TOKEN_ENCRYPT_KEY
        source: "Gerar localmente: 32 bytes aleatórios em hex (64 chars). openssl rand -hex 32. NUNCA commitar."
      - name: SAFE2PAY_WEBHOOK_SECRET
        source: "[ASSUMIDO A4] segredo HMAC do webhook — confirmar no painel/contrato Safe2Pay"
      - name: RSA_PRIVATE_KEY
        source: "Gerar par RSA-2048: openssl genrsa -out key.pem 2048. Privada SÓ no backend, via env."
      - name: RSA_PUBLIC_KEY
        source: "openssl rsa -in key.pem -pubout. Pública servida via GET /v1/payments/chave-publica."
      - name: SAFE2PAY_PAYMENT_URL
        source: "URL do subdomínio payment (cria transações) — adicionar à allowlist SSRF"
      - name: SAFE2PAY_API_URL
        source: "URL do subdomínio api (refund/subconta/saldo) — allowlist SSRF"
      - name: SAFE2PAY_SERVICES_URL
        source: "URL do subdomínio services (consulta status/extrato) — allowlist SSRF"
    dashboard_config:
      - task: "Registrar URL de webhook: POST {dominio}/v1/payments/webhooks/safe2pay"
        location: "Painel Safe2Pay → Webhooks"
      - task: "[ASSUMIDO A1] Confirmar que split/marketplace está habilitado no plano contratado (DEC-003 — ADR supera quando confirmado)"
        location: "Painel/contrato Safe2Pay"
      - task: "Cadastrar/confirmar conta recebedora Jaxegô (recipient para a taxa)"
        location: "Painel Safe2Pay → Subcontas/Recebedores"
---

# PLAN — Phase 10: Safe2Pay núcleo — assinaturas, cobrança com split, escrow, estornos

> Gerado por `gsd-planner` em 2026-06-11.
> Validado por `gsd-plan-checker` em {date} — status: {PASS|BLOCK|FLAG}.
> **⚠ DINHEIRO REAL.** Lei de billing: `docs/SAAS-BILLING-DOCS.md` (CLAUDE.md §18). Tudo Safe2Pay nasce `[ASSUMIDO]` (DEC-003) atrás de `PaymentPort` (ADR-009 v2) + **Stub** — testes NUNCA tocam Safe2Pay real.

## Goal

Entregar o núcleo de pagamento online do Jaxegô via Safe2Pay atrás de interface própria (`PaymentPort` + Stub): cripto de cartão/token, assinatura recorrente cartão/PIX com cron de cobrança e inadimplência, cobrança por entrega com **split** (corrida→escrow do entregador, taxa→Jaxegô+revenue share), **escrow interno 24h**, estornos RN-004, webhooks idempotentes e conciliação diária — mais o checkout web (telas 16 e 12). Money em centavos inteiros, idempotência em toda escrita de cobrança, cartão nunca em texto puro/log.

## Success criteria

Para fechar este plano, TODOS os critérios abaixo devem ser verdes:

- [ ] Round-trip cripto: `decrypt_token(encrypt_token(x)) == x`; `rsa_decrypt_card` decifra blob do cliente; `InvalidTag` levanta erro (nunca retorna blob)
- [ ] `charge_with_split` com soma EXATA: `amount_cents == Σ splits.amount_cents` (invariante testado, residual de arredondamento → Jaxegô)
- [ ] Recusa de cartão/PIX na criação de entrega → entrega NÃO criada (teste F-03 E3)
- [ ] Idempotência: mesma `Reference`/`IdTransaction` → uma única cobrança; webhook duplicado → um efeito (UNIQUE(transaction_id,status))
- [ ] `release_escrow` libera SÓ corridas FINALIZADA+24h aware-UTC sem disputa; disputa nas 24h congela só aquela entrega; idempotente
- [ ] Inadimplência aware-UTC: >10d → blocked, >20d → cancelado; guard de assinatura ativa bloqueia criação de entrega quando blocked/cancelado
- [ ] Estorno escopado por área (sem IDOR → 404 para outro escopo); valor RN-004; conciliação detecta divergência >R$0,01 → alerta
- [ ] Circuit breaker: PaymentPort indisponível → criação card/pix retorna erro tratado; `direct` (Phase 7-9) segue funcionando
- [ ] Subconta cadastrada no gancho de MEI aprovado (Phase 5); sem MEI → sem subconta (degrada para pendência)
- [ ] `alembic upgrade head && alembic downgrade -1` reversível (revision id curto, sem drop_index redundante de FK)
- [ ] Frontend: cartão cifrado RSA-OAEP no cliente nunca vai a estado global/log/analytics; 6 componentes com story claro+escuro; axe-core sem violação crítica nas telas 16/12
- [ ] Nenhum `#hex` em código frontend (Gate 2); zero cartão/CVV/token/api-key em log
- [ ] Todos os testes passam (`cd apps/api && uv run pytest -q`) e frontend (`npm test` / lint)
- [ ] `make lint` limpo; commits atômicos por wave com mensagem padronizada

## REQs referenciados

- REQ-010 — Assinatura recorrente via Safe2Pay (cartão/PIX, status, webhook recorrente idempotente)
- REQ-011 — Limite de plano + upgrade pro-rata / downgrade agendado (RN-028/029)
- REQ-019 — MEI (RN-010 + RN-024): subconta do entregador só com MEI ativo
- REQ-029 — Cancelamento com matriz de custos / estornos (RN-004)
- REQ-034 — Cobrança por entrega cartão/PIX com split Safe2Pay (recusa→não nasce, circuit breaker)
- REQ-036 — Escrow interno 24h (RN-006): FINALIZADA+24h sem disputa

---

## Skills Consultadas

Cada skill abaixo teve regras aplicadas a tasks concretas deste plano.

- `domain/safe2pay-escrow-br` (🔒 obrigatória, 546 linhas) — T-02/T-03/T-06/T-07/T-09: padrão `HasError` (HTTP 200 ≠ sucesso → `_call_safe2pay` central); 3 subdomínios Safe2Pay (`payment` cria / `api` administra / `services` consulta — URLs separadas, nunca concatenar); estados de escrow PENDING→HELD→RELEASED/REFUNDED/FAILED; webhook idempotente por `(transaction_id,status)`; HMAC-SHA256 com `secrets.compare_digest`; rotas distintas de estorno Pix vs Cartão.
- `domain/saas-billing-canonical` + `docs/SAAS-BILLING-DOCS.md` (🔒 CLAUDE.md §18 — lei) — T-01/T-04/T-05: cripto AES-256-GCM token + RSA-OAEP cartão (§4); assinatura recorrente cartão tokenizado / PIX automático (§5-6); guard de assinatura ativa (§9); inadimplência 10/20d (§10); cron diário (§7) com flag de execução; sandbox cobra raw vs produção tokeniza (§13). Mecânica não muda no porte NestJS→FastAPI.
- `owasp-security` (🔒) — T-01/T-02/T-06/T-08: A02 (cripto correta, `compare_digest` anti-timing), A08 (idempotência de webhook/cobrança, anti-replay), A09 (zero cartão/token/segredo em log), A01 (auth de endpoint, IDOR de estorno → 404), A10 (`assert_safe_url` SSRF na chamada ao PSP), A04 (split calculado no backend, nunca frontend).
- `quality/observability-production` (🔒) — T-06/T-08/T-09: conciliação diária com alerta >R$0,01; eventos de cobrança auditados; logs estruturados com `request_id`/`endpoint`/`status_code`/`duration_ms` e redação de campos sensíveis; healthcheck do worker de cobrança.
- `ux-advanced/payment-checkout-ux` (🔒) — T-10/T-11/T-12: valor exato (corrida+taxa ou R$/mês) ANTES de confirmar; um método visível por vez; estado de processamento bloqueante; recusa com causa + saída; anti-dark-pattern no upgrade/downgrade (cancelar de peso igual, sem cronômetro).
- `ux-advanced/trust-safety-ux` (🔒) — T-11: banda de segurança (cadeado + "criptografado · Safe2Pay"); transparência honesta ("a Jaxegô não armazena o número do seu cartão"); nunca pedir dado desnecessário; sem urgência falsa.
- `ux-advanced/form-ux-mastery` + `quality/error-ux-patterns` (🔒) — T-11/T-12: `jx-card-form` com label/erro associado por `aria-describedby`, validação inline (Luhn/validade/CVV) ao blur, autocomplete `cc-*`, `autocomplete="off"` no form do CVV; erro de pagamento com mensagem específica + recuperação.
- `quality/accessibility-pro` (🔒) — T-10/T-11/T-12: AA nos dois temas; `role="radiogroup"` nos métodos; `role="alert"` na recusa; `role="status"`/`aria-live=polite` no PIX aguardando; touch ≥44px; status nunca só por cor; QR com alt + copia-e-cola sempre presente.
- `ux-advanced/design-tokens-system` + `product/component-library-governance` + `ui-ux-pro-max` (🔒 matriz UI) — T-10/T-11/T-12: componentes consomem SÓ a camada semântica `_semantic.scss` (zero `#hex`, Gate 2); valores monetários/IDs em `--jx-font-mono`; 1 acento Fraunces por título; standalone OnPush prefixo `jx-`; nenhum token novo (mapa status reusa `--info/--success/--warning/--error`).
- `ux-advanced/empty-states-polish` (🔒 matriz UI) — T-12: empty state acionável do histórico ("Nenhuma cobrança ainda…"); placeholder honesto "Disponível em breve" para Faturas de taxas (Phase 11), sem dado falso.
- `ux-advanced/dark-mode-theming` (🔒 DEC-001) — T-10/T-11/T-12: AA validado claro E escuro; status como texto vívido sobre `--surface-sunken` (sem token `_bg` pastel novo); stories Storybook em ambos os temas.
- `br/ux-copywriting-ptbr` (🔒 locale pt-BR) — T-11/T-12: copy direta sem "Ops!"/jargão (token/gateway/RSA); valores completos em R$ pt-BR; copy de blocked/estorno/pro-rata exata (§7 do UI-SPEC).
- `product/visual-regression-testing` (🔒 touches 6 componentes novos) — T-12: story obrigatória claro+escuro para os 6 `jx-*` novos; baseline ao fim da fase; nome `{component}-{state}-{theme}-{viewport}.png`.
- `ux-advanced/responsive-breakpoint-strategy` (🔒 web responsivo) — T-10/T-12: breakpoints herdados (320/480/768/1024/1440); checkout centrado max 480px; tela 12 form 620px; CTA sticky acima do teclado no mobile.
- `domain/fastapi-production-patterns` (🔒 has_api) — T-02/T-06/T-08: routers async, `Depends(get_current_user)` + escopo, pydantic v2 `extra="forbid"`, RFC-7807 nos erros, schemas estreitos.
- `product/api-design-contracts` — T-02/T-06/T-08: contratos PaymentPort estáveis (dataclasses frozen), schemas de request/response versionados, idempotência por `Reference`/Idempotency-Key documentada.
- `domain/mysql-schema-design` — T-01: `platform_charges`/`escrow_ledger`/`payment_webhook_events` com PK BIG_ID, UNIQUE de idempotência, índices em FK e em colunas de cron (`finalized_at`, `due_at`); money em INT (centavos), nunca FLOAT.
- `br/lgpd-compliance` — T-06/T-08: CPF/CNPJ de cobrança mascarados em output, nunca em log; `documento_cobranca` com base legal (execução de contrato), entra no pedido de eliminação; dado fiscal preservado sem PII (RN-021).
- `quality/senior-quality-bar` (🔒 Gate 8) — TODAS: zero segredo no repo (env + `.env.example`); zero dupla cobrança (idempotência); zero PII/cartão em log; toda escrita de cobrança com decisão de auth explícita; sem N+1 nos crons (batch); split/escrow atômicos no commit.
- `meta/orchestration-decision-tree` — planejamento: phase de risco alto → squad-research (pré, já feito: RESEARCH.md) e squad-review (pós-execute, recomendado pelo ROADMAP).

## Skills Dispensadas (com justificativa)

- `ux-advanced/gesture-touch-patterns` — checkout é **web** (lojista no desktop/responsivo). Telas mobile do entregador (extrato/saque) são Phase 11. Sem gesto custom aqui.
- `ux-advanced/file-upload-ux` — esta fase não tem upload de arquivo (cartão é cifrado em texto, QR é imagem renderizada de base64 da API).
- `mobile/push-notifications-architecture` — notificação de cobrança/ativação é tratada via webhook→estado→UI polling; sem push novo nesta fase (push é da Phase 8/9).
- `ux-advanced/chat-ux-patterns` — sem chat/mensageria nesta fase.
- `domain/github-actions-ci` — sem mudança de pipeline CI nesta fase (só adiciona testes na suite existente).
- `br/brazilian-forms` — coberta na prática por `ux-advanced/form-ux-mastery` + `jx-field` herdado (máscaras CPF/cartão BR já no componente da Phase 4); citada aqui para registro, não precisa de regra nova.

---

## Tech debt deste plano (verificação obrigatória v0.8+)

| TD ID | Descrição curta | Por que entra (ou não) neste plano | Task que resolve |
|-------|-----------------|-------------------------------------|------------------|
| TD-010 | Naive datetime (risco recorrente auditado) | `urgency_class: pre_launch_high`; prazo lista explicitamente "phase 10". Vencimentos, escrow 24h, inadimplência 10/20d e crons são todos timestamp-críticos. | T-01 (lint custom em `app/payments/*`) + T-04/T-05/T-07 (uso de `ensure_aware_utc`/`UTC_DATETIME`) |
| TD-011 | Broadcast de despacho indisponível | `wont_fix_documented` — pós-M1, não toca pagamento | — |

Nenhuma outra TD tem prazo nesta phase. **Novas TDs criadas por este plano** (DEC-003 / suposições A1-A9 não confirmáveis aqui) listadas na próxima seção e a registrar em `TECH-DEBT.md` ao fechar a fase.

---

## Open questions / LOW confidence do RESEARCH (Regra 12 — destino estruturado)

As 9 suposições do `Assumptions Log` (A1–A9) e DEC-003 são tratadas: **todas atrás do `PaymentPort` + Stub**, marcadas `[ASSUMIDO]` no código, e cada uma vira **task de confirmação com critério de aceite** ou **TD com urgency_class**. Nenhuma fica como "verificar depois" solta.

| Item RESEARCH | Conf. | Resolução neste plano |
|---------------|-------|------------------------|
| A1 — split/marketplace disponível no plano Safe2Pay | LOW (DEC-003) | **T-13** (checkpoint:human-action) "Confirmar split habilitado no contrato/painel"; até lá Stub define o shape e adapter fica `[ASSUMIDO]`. AC de REQ-034: bloqueia ativação em produção, não a implementação. TD-10-01 `pre_launch_blocker`. |
| A2 — formato exato do payload de Split (`Splits:[{Recipient,Amount}]`) | LOW | **T-13** valida via Postman/contrato; T-02 implementa shape `[ASSUMIDO]` isolado no adapter; teste de shape revisável. TD-10-01. |
| A3 — subconta cadastrável via API (`register_subaccount`) | MED | **T-07** implementa `register_subaccount`; se API não suportar, degrada para "pendência de cadastro manual" e o gancho MEI permanece. TD-10-02 `pre_launch_high`. |
| A4 — Safe2Pay fornece HMAC de webhook (`x-safe2pay-signature`) | LOW (segurança) | **T-08** implementa **defesa em profundidade** independente de A4: idempotência (UNIQUE) + allowlist de IP de origem + segredo no path + **nunca liberar dinheiro só pelo webhook** (confirma via `GET /v2/Transaction/{id}` antes de qualquer efeito). **T-13** confirma HMAC nativo. TD-10-03 `pre_launch_blocker`. |
| A5 — prazo de repasse de subconta do PSP | LOW (BAIXO risco) | Decidido por DEC-003: escrow interno 24h é independente do PSP. Sem task — registrado como `[ASSUMIDO]` no docstring de `escrow.py` (T-05). |
| A6 — taxa por transação parametrizável (não fixa pelo PSP) | LOW (BAIXO) | T-06/T-09 `fees.py`: taxa via seed/config, nunca hardcoded; só o valor muda. Sem task de bloqueio. |
| A7 — revenue share default 20% (OQ-1) | LOW (BAIXO) | T-06 `fees.py`: parametrizado por área (seed), default 20%; trocável sem código. Sem superfície de UI (relatório é Phase 13). |
| A8 — cálculo anual = mensal × 10 (2 meses grátis) | LOW (BAIXO) | T-04 `subscriptions.py`: política de desconto via seed; ajustar sem código. |
| A9 — endpoints exatos de estorno (Pix vs Cartão) | MED | **T-13** confirma via Postman; T-06 isola URLs por subdomínio no adapter `[ASSUMIDO]`. TD-10-04 `pre_launch_high`. |

**DEC-003 trava A1/A2/A4/A9** (bloqueiam produção, não implementação). ADR de confirmação supera DEC-003 quando o contrato Safe2Pay chegar. **TDs a registrar ao fechar a fase:** TD-10-01 (split `pre_launch_blocker`), TD-10-02 (subconta `pre_launch_high`), TD-10-03 (HMAC webhook `pre_launch_blocker`), TD-10-04 (endpoints estorno `pre_launch_high`).

---

## Threat model

Herdado verbatim do `## Security Baseline` do `RESEARCH.md` (Regra 7). Cada TH é verificável no `secure-phase`.

| ID | Ameaça | Vetor | Impacto | Likelihood | Mitigação | Task |
|----|--------|-------|---------|------------|-----------|------|
| TH-A | Cartão em texto puro / em log (PCI-adjacent) | Frontend→backend | Crítico | Médio | RSA-OAEP-2048 no cliente; backend decifra só em memória; `{numeroCartao,cvv}` nunca persistidos/logados; filtro structlog mascara `card/cvv/numeroCartao` | T-01, T-11 |
| TH-B | Token de cartão em repouso legível | Tampering | Alto | Baixo | AES-256-GCM `base64(nonce12+ct_com_tag)`; chave 32B só env; decifrar só no cron; `InvalidTag`→erro | T-01, T-04 |
| TH-C | Segredos no repo (api-key, chaves cripto, webhook secret) | Info Disclosure | Crítico | Médio | Todos via env (`Field default None`); `.env.example` placeholders; `.env` no `.gitignore`; segredo commitado = ROTACIONAR. Gate 8 FAIL-BLOCK | T-01 (config) |
| TH-D | Dupla cobrança / cobrança duplicada | Tampering/Repudiation | Crítico | Médio | Idempotency key + `Reference`/`IdTransaction`; `platform_charges` UNIQUE; webhook UNIQUE(tx,status); recobrança só se charge aberto | T-01, T-06, T-08 |
| TH-E | Webhook forjado / sem auth (libera dinheiro falso) | Spoofing/Tampering | Crítico | Médio | Ordem: log→HMAC `compare_digest`→dedup→enfileira→200. `[ASSUMIDO A4]`: allowlist IP + segredo no path + nunca liberar escrow só pelo webhook (confirma via `GET Transaction/{id}`); anti-replay | T-08 |
| TH-F | Integridade do split (soma ≠ Amount) | Tampering | Alto | Médio | Split SÓ no backend (frontend nunca manda valores); centavos inteiros; invariante `amount_cents == Σ splits` testado; residual → Jaxegô | T-06 |
| TH-G | Escrow liberado cedo / indevido | Elevation/Tampering | Crítico | Baixo | Release só via cron `release_escrow` com FINALIZADA+24h aware-UTC sem disputa; nunca via endpoint do usuário; transição atômica; idempotente (só se HELD) | T-05 |
| TH-H | Estorno de cobrança alheia (IDOR) / valor errado | Elevation/Tampering | Alto | Médio | Escopo no WHERE (`area_id=user.area_id`), 404 (não 403); valor RN-004 calculado no backend; só charge estornável | T-06 |
| TH-I | Conciliação cega (divergência extrato×registros) | Repudiation/Tampering | Alto | Médio | Job diário compara extrato×`platform_charges`; >R$0,01 → alerta admin (não auto-corrige); centavos, comparação exata | T-09 |
| TH-J | Race em cobrança/liberação (cron paralelo) | Tampering | Alto | Baixo | Cron idempotente (estado-guard: só `situacao=0`/`HELD`); `SELECT ... FOR UPDATE` ou flag de execução; UNIQUE impede efeito duplo | T-04, T-05 |
| TH-K | PII/LGPD de cobrança (CPF/CNPJ, e-mail, telefone) | Info Disclosure | Médio | Médio | CPF/CNPJ mascarados em output, nunca em log; base legal execução de contrato; retenção definida; dado fiscal sem PII (RN-021) | T-06, T-08 |
| TH-L | SSRF na chamada ao PSP / redirect | A10 | Alto | Baixo | `assert_safe_url` com allowlist dos 3 subdomínios antes de conectar e pós-redirect; `build_client(follow_redirects=False)` | T-02 |
| TH-M | Endpoint sem decisão de auth | A01 | Alto | Médio | Checkout/assinatura: `Depends(get_current_user)`+escopo; webhook/chave-pública: `# público:` justificado; cron: arq in-process | T-02, T-06, T-08 |

---

## Performance budget

Herdado de `.planning/config.json > performance_budget`.

**Frontend** (telas 16 e 12):
- LCP ≤ 2500ms · INP ≤ 200ms · CLS ≤ 0.1 · Bundle main.js ≤ 400kb gzip
- Lazy loading: rota `/plano` e `/nova-entrega` lazy; `jx-card-form`/`jx-pix-qr` carregados sob demanda do método selecionado
- Ferramenta: Lighthouse CI no pipeline (telas 16/12)

**Backend** (endpoints + crons):
- p95 checkout/assinatura ≤ 800ms (exclui latência do PSP, que é assíncrona via webhook); p99 ≤ 1500ms
- Webhook responde 200 em < 5s (trabalho pesado enfileirado em arq — D-04)
- N+1: zero no histórico de cobranças e nos crons (batch query, `selectinload`); conciliação processa extrato em lote
- Crons (`charge_subscriptions_daily`, `release_escrow`, `reconcile_safe2pay`) idempotentes; sem chamar Safe2Pay dentro de transação de banco aberta
- Ferramenta: pytest-benchmark em `test_split`/`test_escrow`; structlog `duration_ms` em prod

---

## Observability checklist (endpoints + crons + webhooks)

Aplicando `quality/observability-production`:

- [ ] Todo endpoint de pagamento loga: `request_id`, `user_id`, `endpoint`, `method`, `status_code`, `duration_ms`
- [ ] **NUNCA logar:** `numeroCartao`, `cvv`, `validade`, `nomeTitular`, token AES, `SAFE2PAY_API_KEY`, blob RSA, CPF/CNPJ de cobrança (filtro structlog central mascara esses campos — TH-A/TH-K)
- [ ] Erros 4xx → WARNING; 5xx → ERROR + alert no canal de monitoramento
- [ ] `HasError` da Safe2Pay logado como `safe2pay_business_error` com `error_code` (sem payload de cartão)
- [ ] Webhook: logar payload em `payment_webhook_events` ANTES de processar (sem PII de cartão); assinatura inválida → WARNING `safe2pay_webhook_bad_signature`
- [ ] **Conciliação diária:** divergência extrato×`platform_charges` >R$0,01 → ERROR + alerta admin plataforma (TH-I); evento auditado
- [ ] Eventos de cobrança auditados: criação de charge, hold/release de escrow, estorno, mudança de status de assinatura (com `transaction_id`, sem PII)
- [ ] Crons logam contagem processada/liberada/conciliada; queries >200ms → WARNING
- [ ] `/healthz` reflete worker arq de cobrança ativo

---

## Error UX checklist (UI — telas 16 e 12)

Aplicando `quality/error-ux-patterns`:

- [ ] Cartão recusado (assinatura): "Não foi possível processar este cartão. Confira os dados ou use outro cartão. Você também pode pagar por PIX." (causa + alternativas)
- [ ] **Cartão recusado (entrega F-03 E3):** `role="alert"` "Cartão recusado. A entrega não foi criada." + 2 saídas de peso igual: "Tentar de novo" e "Pagar direto ao entregador" (troca para `direct` sem perder o form)
- [ ] PIX expirado: "Esse código PIX expirou. Gere um novo para continuar." (recuperável → regenera)
- [ ] Inadimplência (blocked >10d): banner `--error` `role="alert"` explicando causa + consequência (cancelado >20d) + CTA "Regularizar pagamento"
- [ ] Validação inline ao blur (Luhn/validade/CVV), não modal ao submit; erro associado `aria-describedby`/`aria-invalid`
- [ ] Erro de rede no checkout → retry com feedback visual; sem "Algo deu errado" genérico
- [ ] Toast (sucesso copiar PIX, pagamento confirmado) vs inline (erro de campo) vs banner (status de negócio): consistente com Phase 3 `jx-notice`

---

## Integration contracts (integration_check: TRUE — validado por Stub, NUNCA Safe2Pay real — Gate 5)

Contratos cross-layer validados pelo `gsd-integration-checker` após execução. **Toda validação roda contra `PaymentStubAdapter`** (D-09); a impl httpx real só em staging/prod com conta Safe2Pay.

| Contrato | Consumer | Provider | Assertion |
|----------|----------|----------|-----------|
| GET /v1/payments/chave-publica | apps/web/.../payment-crypto.service.ts | apps/api/app/payments/router.py | resposta tem `public_key` PEM; cliente cifra cartão RSA-OAEP antes de qualquer POST |
| POST /v1/payments/assinar | apps/web/.../billing.service.ts | apps/api/app/payments/router.py | body tem `metodo` ∈ {card,pix} + `card_blob`(RSA) ou nada (PIX); resposta tem `status`, `qr_code?`, `next_due_at` |
| POST /v1/deliveries (card/pix) | apps/web/.../delivery-payment.service.ts | apps/api/app/deliveries/service.py → payments/service.charge_delivery | recusa → 4xx e entrega NÃO criada (F-03 E3); aprovado → 201 com `delivery_id` + estado CRIADA |
| POST /v1/payments/webhooks/safe2pay | Safe2Pay (Stub injeta evento) | apps/api/app/payments/webhooks_router.py | log antes de processar; HMAC inválido → 403; duplicado (mesmo tx,status) → 200 idempotente, 1 efeito |
| PaymentPort.charge_with_split | apps/api/app/payments/service.py | StubAdapter / Safe2PayHttpAdapter | `amount_cents == Σ splits.amount_cents`; recusa levanta erro tratado; `HasError`→PaymentGatewayError |
| PaymentPort.refund | apps/api/app/payments/service.py | StubAdapter / Safe2PayHttpAdapter | rota distinta Pix vs Cartão; ownership por área no caller; valor RN-004 |
| PaymentPort.register_subaccount | apps/api/app/couriers/service.py (MEI aprovado) | StubAdapter / Safe2PayHttpAdapter | retorna `recipient_id`; sem MEI → não chamado; API ausente → degrada para pendência |
| Circuit breaker | apps/api/app/deliveries/service.py | payments/service | PaymentPort indisponível → erro tratado em card/pix; `direct` segue 201 |

---

## Tasks

> Cada task code-producing usa `tdd="true"` quando há contrato testável (RED→GREEN). Stub determinístico nos testes; **NUNCA chamar Safe2Pay real** (D-09).

### T-00 — Wave 0: scaffold de testes + Stub + lint de naive datetime

- **Type:** test
- **Files:** `apps/api/tests/payments/conftest.py`, `apps/api/tests/payments/test_*.py` (todos os listados), lint custom naive datetime cobrindo `app/payments/*`
- **Skills aplicadas:** `domain/safe2pay-escrow-br` (Stub determinístico sem rede); `quality/senior-quality-bar` (Nyquist: teste antes de código); `meta` TD-010 (lint naive datetime)
- **Descrição:** Criar `conftest.py` com fixture `PaymentStubAdapter` + override do factory (NUNCA rede). Criar os arquivos de teste como esqueleto RED (asserts de comportamento esperado, falham por ausência de impl). Estender o lint custom que proíbe `datetime.now()` naive / `.replace(tzinfo=None)` para cobrir `app/payments/*` (TD-010).
- **Success:** `pytest tests/payments -q` coleta todos os testes (RED, falham por impl ausente); fixture Stub não toca rede; lint roda em `app/payments/*`.
- **Verify:** `<automated>cd apps/api && uv run pytest tests/payments --collect-only -q</automated>`
- **Depends on:** none

### T-01 — Cripto + migration 0009 + config/env (FUNDAÇÃO)

- **Type:** migration + new_module
- **Files:** `app/payments/crypto.py`, `app/payments/models.py`, `app/payments/errors.py`, `app/core/config.py`, `app/merchants/models.py`, `apps/api/.env.example`, `alembic/versions/0009_safe2pay_billing_escrow.py`
- **Skills aplicadas:** `saas-billing-canonical`/SAAS-BILLING §4 (cripto); `owasp-security` A02/A09 (cripto correta, segredos só env); `domain/mysql-schema-design` (schema, UNIQUE idempotência, índices de cron); `senior-quality-bar` (Gate 8: segredos)
- **tdd:** true
- **behavior:**
  - `decrypt_token(encrypt_token("tok_x")) == "tok_x"`; formato é `base64(nonce[12] + ciphertext_que_JÁ_inclui_tag)` — NÃO replicar layout `iv+tag+ct` do Node (Pitfall 1)
  - `rsa_decrypt_card(blob_cifrado_pela_publica)` retorna JSON do cartão; chave privada só de env
  - token adulterado → `InvalidTag` → `RuntimeError` (NUNCA retorna o blob — não portar o legado texto-puro do Node)
  - `_token_key()` rejeita chave != 64 hex chars
  - `alembic upgrade head` cria `platform_charges`, `escrow_ledger`, `payment_webhook_events` + colunas de assinatura recorrente em `merchant_subscriptions` (estado trial/active/blocked/cancelado, token AES, `due_at` aware-UTC, método); `alembic downgrade -1` reverte tudo
- **Descrição:** `crypto.py` com `AESGCM` (token) + `padding.OAEP`/SHA-256 (cartão) via lib `cryptography` (já instalada). `models.py` com as 3 tabelas novas (BIG_ID, UTC_DATETIME, AreaScopedMixin; money em INT centavos; `platform_charges` UNIQUE(idempotency_key) e índice em `transaction_id`; `escrow_ledger` com FK delivery/courier + estado HELD/RELEASED/REFUNDED/FROZEN + índice em `finalized_at`; `payment_webhook_events` UNIQUE(transaction_id, status)). Estender `merchant_subscriptions` (edit em `merchants/models.py`). `config.py`: 8 segredos novos com `Field(default=None)` + allowlist dos 3 subdomínios. `.env.example` com placeholders. Migration **reversível**, revision id curto `0009_safe2pay_billing_escrow` (≤32 chars sem ext), `down_revision="0008_proofs_tracking_notif"`, `downgrade()` dropa tabelas/colunas; **não emitir `drop_index` redundante de FK** (lição Phase 7).
- **Success:** round-trip cripto verde; `InvalidTag`→erro; migration up+down reversível no CI; zero segredo no repo (grep limpo); `.env.example` completo.
- **Verify:** `<automated>cd apps/api && uv run pytest tests/payments/test_crypto.py -x && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head</automated>`
- **Depends on:** T-00

### T-02 — PaymentPort + Safe2PayHttpAdapter + Stub + factory

- **Type:** new_module
- **Files:** `app/payments/port.py`, `app/payments/safe2pay_adapter.py`, `app/payments/safe2pay_stub.py`, `app/payments/factory.py`
- **Skills aplicadas:** `domain/safe2pay-escrow-br` (`_call_safe2pay` SEMPRE checa `HasError`; 3 subdomínios; nunca concatenar subdomínio); `owasp-security` A10 (`assert_safe_url` SSRF, `follow_redirects=False`); `product/api-design-contracts` (Protocol estável, dataclasses frozen); `domain/fastapi-production-patterns`
- **tdd:** true
- **behavior:**
  - `_call_safe2pay` com resposta `{"HasError": true}` (mesmo HTTP 200) → `PaymentGatewayError` (não cria charge órfã — Pitfall 2)
  - `assert_safe_url` rejeita URL fora da allowlist dos 3 subdomínios (TH-L)
  - `PaymentStubAdapter` é determinístico, sem rede; `factory.get_payment_adapter()` retorna Stub quando `_use_stub()` (igual padrão `integrations/factory.py`)
  - `ChargeResult`/`Split` carregam `amount_cents` inteiro
- **Descrição:** `port.py` = `PaymentPort` Protocol + dataclasses (`ChargeResult`, `Split`, `CardData`, `Customer`, `StatementEntry`) — replica o padrão `app/integrations/base.py`. `safe2pay_adapter.py` = impl httpx com `_call_safe2pay` central (raise_for_status + checagem `HasError`, log SEM payload), 3 base URLs (`PAYMENT_URL`/`API_URL`/`SERVICES_URL`), `[ASSUMIDO]` no shape de Split/estorno (A2/A9). `safe2pay_stub.py` = Stub que materializa o shape assumido para dev/test. `factory.py` = `get_payment_adapter()` com `_use_stub()` reaproveitado.
- **Success:** `HasError` levanta erro; SSRF bloqueia URL não-allowlisted; Stub sem rede; factory retorna Stub em test.
- **Verify:** `<automated>cd apps/api && uv run pytest tests/payments/test_adapter_haserror.py -x</automated>`
- **Depends on:** T-01

### T-03 — repo + service base (orquestração + idempotência)

- **Type:** new_module
- **Files:** `app/payments/repo.py`, `app/payments/service.py`, `app/payments/schemas.py`
- **Skills aplicadas:** `owasp-security` A08 (idempotência por idempotency_key/`Reference`), A04 (split no backend); `domain/fastapi-production-patterns` (pydantic v2 `extra="forbid"`); `product/api-design-contracts`
- **tdd:** true
- **behavior:**
  - `record_charge` com mesma `idempotency_key` → uma única linha em `platform_charges` (UNIQUE → upsert/no-op idempotente — TH-D)
  - `schemas` rejeitam campos extras (`extra="forbid"`); `card_blob` aceito como string opaca (nunca campos de cartão crus no schema)
  - `service` depende do Protocol `PaymentPort`, nunca da impl
- **Descrição:** `repo.py` com queries de `platform_charges`/`escrow_ledger`/`webhook_events` (sem N+1, índices usados). `service.py` orquestra (depende de `PaymentPort` injetado pelo factory). `schemas.py` pydantic v2 estreitos (`extra="forbid"`, `card_blob` opaco).
- **Success:** idempotência de `record_charge` verde; schema rejeita extras; service sem acoplamento à impl.
- **Verify:** `<automated>cd apps/api && uv run pytest tests/payments/test_split.py::test_idempotent_charge -x</automated>`
- **Depends on:** T-02

### T-04 — Assinatura recorrente + cron de cobrança + inadimplência + guard + upgrade/downgrade

- **Type:** new_module + background_job
- **Files:** `app/payments/subscriptions.py`, `app/workers/tasks.py` (edit: `charge_subscriptions_daily`, `schedule_pix_charges`, `sync_delinquency`), `app/workers/settings.py` (edit: cron_jobs)
- **Skills aplicadas:** `saas-billing-canonical`/SAAS-BILLING §5-10 (recorrente cartão/PIX, inadimplência 10/20d, guard, sandbox vs prod §13); `owasp-security` A08 (cron idempotente, flag executando — TH-J); TD-010 (aware-UTC); `quality/observability-production`
- **tdd:** true
- **behavior:**
  - `classify_delinquency`: >20d → "cancelado", >10d → "blocked", senão "active"; `days_overdue` usa `ensure_aware_utc` (TD-010 — Pitfall 4)
  - cron de cobrança idempotente (só `situacao=0`/aberto; flag executando evita race — TH-J)
  - guard: assinatura blocked/cancelado bloqueia criação de entrega
  - upgrade pro-rata calculado em centavos (REQ-011, RN-029); downgrade agendado para fim do ciclo (sem cobrança agora)
  - tokeniza→cobra em produção; sandbox cobra raw; recorrência sempre `IsSandbox:false` (Pitfall 5) — testado via Stub
- **Descrição:** `subscriptions.py` (ativação cartão tokenizado / PIX automático, estados, pro-rata/downgrade RN-029, guard). Crons `charge_subscriptions_daily`/`schedule_pix_charges`/`sync_delinquency` em `tasks.py`, registrados em `settings.cron_jobs` (ao lado de `finalize_deliveries` Phase 9). `[ASSUMIDO A8]` desconto anual = mensal×10 (seed).
- **Success:** inadimplência 10/20d aware-UTC; guard bloqueia; pro-rata em centavos; cron idempotente.
- **Verify:** `<automated>cd apps/api && uv run pytest tests/payments/test_subscription.py tests/payments/test_delinquency.py tests/payments/test_plan_change.py -x</automated>`
- **Depends on:** T-03

### T-05 — Escrow interno 24h (ledger hold/release/freeze + cron)

- **Type:** new_module + background_job
- **Files:** `app/payments/escrow.py`, `app/workers/tasks.py` (edit: `release_escrow`), `app/workers/settings.py` (edit: cron_jobs)
- **Skills aplicadas:** `domain/safe2pay-escrow-br` (state machine PENDING→HELD→RELEASED/FROZEN); `owasp-security` A01/A08 (release só via cron, atômico, idempotente — TH-G); TD-010 (aware-UTC 24h); RN-006
- **tdd:** true
- **behavior:**
  - `release_escrow` libera SÓ holds com `finalized_at <= now(UTC)-24h` e sem disputa aberta (reusa FINALIZADA Phase 9)
  - disputa aberta dentro das 24h → FREEZE só daquela entrega; demais seguem (F-07 E4)
  - transição atômica: `mark_released` + `credit_courier_balance` no mesmo commit
  - idempotente: só libera se ainda `HELD` (race-safe — TH-G/TH-J)
  - cutoff usa `datetime.now(UTC)` aware (TD-010)
- **Descrição:** `escrow.py` com `hold()`/`release_escrow()`/`freeze()`. Cron `release_escrow` registrado em `settings.cron_jobs`, reusando o gatilho FINALIZADA da Phase 9 (`finalize_deliveries`). Saldo sacável só alimentado aqui (saque é Phase 11).
- **Success:** release só FINALIZADA+24h sem disputa; freeze isolado; atômico; idempotente.
- **Verify:** `<automated>cd apps/api && uv run pytest tests/payments/test_escrow.py -x</automated>`
- **Depends on:** T-03

### T-06 — Cobrança split por entrega + fees + estornos + wiring na criação (card/pix ATIVO) + circuit breaker

- **Type:** new_endpoint + integration
- **Files:** `app/payments/service.py` (edit: `charge_delivery`, `refund`), `app/payments/fees.py`, `app/payments/router.py`, `app/deliveries/service.py` (edit: ativa card/pix + circuit breaker)
- **Skills aplicadas:** `domain/safe2pay-escrow-br` (split corrida/taxa, estorno Pix vs Cartão); `owasp-security` A04 (split no backend — TH-F), A01 (estorno escopado, 404 não 403 — TH-H), A10; RN-004 (estorno), RN-023 (taxa nas 3 modalidades); `quality/error-ux-patterns` (recusa→não nasce); `br/lgpd-compliance` (CPF mascarado — TH-K)
- **tdd:** true
- **behavior:**
  - `charge_delivery`: `Amount = corrida + taxa`; splits `[entregador:corrida, jaxego:taxa+rev_share]`; invariante `amount_cents == Σ splits` (residual de arredondamento → Jaxegô — Pitfall 6/TH-F)
  - recusa do PaymentPort na criação → entrega NÃO criada (F-03 E3 — teste explícito)
  - cobrança grava `platform_charges` (idempotency key + `Reference=dlv_{id}`) + cria hold no escrow
  - estorno: rota Pix vs Cartão (A9 `[ASSUMIDO]`); escopo por área no WHERE → 404 para outra área (TH-H); valor RN-004 (pré-aceite total, pós-coleta 100%+retorno)
  - `fees.py`: taxa via seed/config (A6), revenue share por área default 20% (A7), nunca hardcoded
  - circuit breaker: PaymentPort indisponível → erro tratado em card/pix; `direct` segue criando (REQ-034)
- **Descrição:** `fees.py` (taxa + revenue share parametrizados). `charge_delivery`/`refund` em `service.py`. `router.py` com endpoints de cobrança/estorno (`Depends(get_current_user)`+escopo merchant/área). Edit em `deliveries/service.py`: ativa o caminho card/pix (Phase 7 reaberto) chamando `payments.service.charge_delivery`; circuit breaker isola card/pix sem afetar `direct`.
- **Success:** soma exata do split; recusa→não nasce (F-03 E3); idempotência por Reference; estorno sem IDOR; circuit breaker preserva direto.
- **Verify:** `<automated>cd apps/api && uv run pytest tests/payments/test_split.py tests/payments/test_refund.py tests/payments/test_circuit_breaker.py -x</automated>`
- **Depends on:** T-04, T-05

### T-07 — Subconta do entregador (gancho MEI aprovado — Phase 5)

- **Type:** integration
- **Files:** `app/couriers/service.py` (edit: gancho MEI aprovado → `register_subaccount`)
- **Skills aplicadas:** `domain/safe2pay-escrow-br` (cadastro de recebedor/subconta); RN-010 (MEI p/ repasse); `owasp-security` A09 (CNPJ/PIX key fora de log)
- **tdd:** true
- **behavior:**
  - MEI aprovado no KYC (Phase 5) → `PaymentPort.register_subaccount(courier_id, mei_cnpj, pix_key)` → salva `s2p_recipient_id` no courier
  - sem MEI → não chama; `[ASSUMIDO A3]` se API não suportar → degrada para "pendência de cadastro manual" (não quebra o fluxo); gancho MEI permanece
  - sem subconta → entrega card/pix do entregador não repassa via plataforma (direto da Phase 7-9 continua)
- **Descrição:** Edit no `couriers/service.py` no ponto de aprovação do MEI (gancho `mei_pending`→ativo, Phase 5): dispara cadastro de subconta via `PaymentPort`. Estado degradado registrado se API ausente (A3).
- **Success:** subconta cadastrada no MEI aprovado; sem MEI → sem subconta; degradação graciosa.
- **Verify:** `<automated>cd apps/api && uv run pytest tests/payments/test_split.py::test_subaccount_on_mei_approval -x</automated>`
- **Depends on:** T-02

### T-08 — Webhooks Safe2Pay idempotentes (log→HMAC→dedup→fila→200) + defesa em profundidade

- **Type:** new_endpoint + background_job
- **Files:** `app/payments/webhooks_router.py`, `app/workers/tasks.py` (edit: `process_safe2pay_event`), `app/main.py` (edit: registra router público)
- **Skills aplicadas:** `domain/safe2pay-escrow-br` (idempotência por `(tx,status)`, HMAC `compare_digest`); `owasp-security` A08 (anti-replay, valida antes de efeito — TH-E), A01; `quality/observability-production` (log antes de processar); SAAS-BILLING §8
- **tdd:** true
- **behavior:**
  - ordem obrigatória: log payload → valida HMAC (`secrets.compare_digest`, NUNCA `==`) → dedup `already_processed(tx,status)` → enfileira arq → 200 < 5s
  - HMAC inválido → 403; webhook duplicado (mesmo tx,status) → 200 idempotente, **um** efeito (Pitfall 3 — TH-E)
  - **defesa em profundidade A4 `[ASSUMIDO]`:** allowlist de IP de origem + segredo no path + **nunca liberar escrow só pelo webhook** → confirma via `GET /v2/Transaction/{id}` antes de qualquer efeito financeiro; anti-replay por janela/timestamp
  - erro de negócio no processamento → logar+enfileirar+200 (nunca 500 — Safe2Pay reenviaria infinitamente)
  - endpoint público com `# público: idempotência+HMAC+confirmação por GET cobrem auth` (TH-M)
- **Descrição:** `webhooks_router.py` endpoint público. `process_safe2pay_event` (worker) faz o trabalho pesado: confirma status via `GET` antes de efeito, atualiza charge/assinatura, dispara hold/release conforme o evento. Registra router em `main.py`.
- **Success:** duplicado → 1 efeito; HMAC inválido → 403; nunca libera dinheiro só pelo webhook; 200 < 5s.
- **Verify:** `<automated>cd apps/api && uv run pytest tests/payments/test_webhooks.py -x</automated>`
- **Depends on:** T-04, T-05

### T-09 — Conciliação diária (extrato × platform_charges → alerta)

- **Type:** background_job
- **Files:** `app/payments/reconcile.py`, `app/workers/tasks.py` (edit: `reconcile_safe2pay`), `app/workers/settings.py` (edit: cron_jobs)
- **Skills aplicadas:** `quality/observability-production` (alerta de divergência); `domain/safe2pay-escrow-br` (`get_statement` via subdomínio `services`); SAAS-BILLING / integracoes.md §1 (D-08 — TH-I)
- **tdd:** true
- **behavior:**
  - `reconcile_safe2pay` compara extrato Safe2Pay (`PaymentPort.get_statement`) × `platform_charges`; diferença **>R$0,01** (1 centavo) → alerta admin plataforma (não auto-corrige — TH-I)
  - comparação em centavos inteiros, exata; aware-UTC na janela (since/until)
  - cron registrado em `settings.cron_jobs`
- **Descrição:** `reconcile.py` com a lógica de conciliação; cron diário. Alerta via canal de observabilidade (ERROR), sem corrigir automaticamente.
- **Success:** divergência >R$0,01 detectada e alertada; comparação exata em centavos.
- **Verify:** `<automated>cd apps/api && uv run pytest tests/payments/test_reconcile.py -x</automated>`
- **Depends on:** T-02

### T-10 — Frontend: serviços de billing/cripto + tela 16 (plano/assinatura) shell + status + histórico

- **Type:** ui_component
- **Files:** `apps/web/.../plano/plano.page.ts`, `payment-crypto.service.ts`, `billing.service.ts`, `components/jx-subscription-status.component.ts`, `components/jx-charge-history.component.ts`
- **Skills aplicadas:** matriz UI (`design-tokens-system`/`component-library-governance`/`ui-ux-pro-max` — só camada semântica, zero `#hex`, valores em mono); `accessibility-pro` (status nunca só por cor, AA dois temas); `dark-mode-theming` (DEC-001); `empty-states-polish` (histórico vazio acionável); `data-tables-ux` (`jx-data-table` reuso); `responsive-breakpoint-strategy`; `br/ux-copywriting-ptbr` (copy §7)
- **Descrição:** `payment-crypto.service.ts` busca `GET /v1/payments/chave-publica` e cifra cartão RSA-OAEP no cliente (texto puro NUNCA sai do componente). `billing.service.ts` consome assinatura/planos/histórico. `jx-subscription-status` (trial/active/blocked/cancelado — mapa §3, ícone+rótulo+valor mono). `jx-charge-history` (reusa `jx-data-table`; empty acionável; "Faturas de taxas" placeholder "Disponível em breve" Phase 11). `plano.page.ts` monta a tela 16 (loading skeleton, error retry).
- **Success:** status com 4 variantes sem color-only; histórico empty acionável; cripto no cliente; zero `#hex`; axe-core sem violação crítica.
- **Verify:** `<automated>cd apps/web && npm test -- --include="**/plano/**" && npm run lint</automated>`
- **Depends on:** T-06 (contrato de endpoints)

### T-11 — Frontend: checkout cartão (RSA) + PIX QR + method toggle (telas 16 + reuso 12)

- **Type:** ui_component
- **Files:** `components/jx-checkout-method-toggle.component.ts`, `components/jx-card-form.component.ts`, `components/jx-pix-qr.component.ts`
- **Skills aplicadas:** `ux-advanced/payment-checkout-ux` (valor exato antes; um método por vez; processando bloqueante; recusa+saída); `trust-safety-ux` (banda de segurança, transparência); `form-ux-mastery`+`error-ux-patterns` (label/erro, Luhn/validade/CVV inline, autocomplete `cc-*`, `autocomplete=off` CVV); `accessibility-pro` (radiogroup, alert, status, ≥44px, QR alt + copia-e-cola); `br/ux-copywriting-ptbr`; `dark-mode-theming`
- **Descrição:** `jx-checkout-method-toggle` (radios cartão/PIX, banda de segurança). `jx-card-form` — cifra `{nomeTitular,numeroCartao,validade,cvv}` com RSA-OAEP **no cliente** antes de enviar; texto puro nunca vai a estado global/log/analytics; validação inline; estados idle/cifrando/aprovado/recusado. `jx-pix-qr` — renderiza QR base64 + copia-e-cola (mono) + deep link; estado aguardando com `aria-live` + polling; expirado → regenera.
- **Success:** cartão cifrado no cliente; CVV não persistido; recusa com causa+alternativa PIX; PIX aguardando acessível; ≥44px; nenhum `#hex`.
- **Verify:** `<automated>cd apps/web && npm test -- --include="**/jx-card-form**" --include="**/jx-pix-qr**"</automated>`
- **Depends on:** T-10

### T-12 — Frontend: upgrade/downgrade + nova-entrega card/pix ativo (F-03 E3) + stories visual regression

- **Type:** ui_component
- **Files:** `components/jx-plan-compare.component.ts`, `apps/web/.../nova-entrega/nova-entrega.page.ts`, `delivery-payment.service.ts`, stories Storybook dos 6 componentes novos
- **Skills aplicadas:** `payment-checkout-ux` (anti-dark-pattern: cancelar peso igual, sem cronômetro, pro-rata valor exato); `error-ux-patterns` (F-03 E3 recusa→não nasce, retry/trocar p/ direto); `visual-regression-testing` (6 stories claro+escuro); `accessibility-pro`; `br/ux-copywriting-ptbr` (copy pro-rata/downgrade/estorno §7); `responsive-breakpoint-strategy`
- **Descrição:** `jx-plan-compare` (reusa `jx-plan-card`; upgrade pro-rata com painel de confirmação; downgrade agendado; anti-dark-pattern). Edit `nova-entrega.page.ts`: ativa radios PIX/cartão (Phase 7 "em breve" → ATIVO); cartão → `jx-card-form` inline; PIX → `jx-pix-qr`; `jx-estimate-box` mostra corrida+taxa antes de confirmar; **F-03 E3:** recusa → `role="alert"` "Cartão recusado. A entrega não foi criada." + "Tentar de novo"/"Pagar direto" (peso igual, troca para `direct` sem perder form). Stories Storybook (claro+escuro) dos 6 `jx-*` novos.
- **Success:** F-03 E3 recusa→não nasce com 2 saídas; upgrade/downgrade sem dark-pattern; 6 stories claro+escuro; valor exato antes de confirmar.
- **Verify:** `<automated>cd apps/web && npm test -- --include="**/nova-entrega/**" --include="**/jx-plan-compare**" && npm run build-storybook</automated>`
- **Depends on:** T-11

### T-13 — checkpoint: confirmar contrato Safe2Pay (split/HMAC/estorno/subconta) — DEC-003

- **Type:** checkpoint:human-action
- **Gate:** blocking (para ativação em produção; NÃO bloqueia a execução em dev/test com Stub)
- **what-built:** Toda a integração Safe2Pay implementada e testada contra Stub. As suposições A1/A2/A4/A9 (split disponível+formato, HMAC nativo de webhook, endpoints de estorno) estão `[ASSUMIDO]` (DEC-003), isoladas atrás do `PaymentPort`.
- **how-to-verify (humano, com o contrato/Postman Safe2Pay real):**
  1. Confirmar que split/marketplace está habilitado no plano contratado (A1) — painel/contrato.
  2. Validar o shape exato do payload de Split (`Splits:[{Recipient,Amount}]`?) via Postman (A2).
  3. Confirmar se Safe2Pay assina o webhook (header HMAC) ou se a defesa em profundidade (IP allowlist + segredo no path + confirmação por GET) é o caminho definitivo (A4).
  4. Confirmar endpoints exatos de estorno Pix vs Cartão (A9).
  5. Confirmar se subconta é cadastrável via API (A3) ou exige cadastro manual no painel.
  - Para cada divergência → abrir **ADR que supera DEC-003** e ajustar APENAS a impl do adapter (não o domínio).
- **resume-signal:** "contrato confirmado" (com ADR) ou "manter Stub/`[ASSUMIDO]` — produção bloqueada" (registra TD-10-01/03 como `pre_launch_blocker`).
- **Depends on:** T-06, T-08 (precisa do adapter implementado para confrontar com o contrato real)

---

## Execution order

Waves (grupos paralelizáveis; same-wave = zero overlap de arquivo):

- **Wave 0:** T-00 (scaffold de testes + Stub + lint naive datetime) — fundação de teste, RED
- **Wave 1:** T-01 (cripto + migration + config) — fundação de dados/cripto
- **Wave 2 (paralelo):** T-02 (PaymentPort + adapters), T-09-prep não — apenas T-02 (todos os outros dependem dele)
- **Wave 3 (paralelo):** T-03 (repo+service+schemas), T-07 (subconta MEI — só depende de T-02), T-09 (conciliação — só depende de T-02)
- **Wave 4 (paralelo):** T-04 (assinatura+cron+inadimplência), T-05 (escrow) — ambos dependem de T-03, sem overlap de arquivo entre si exceto `workers/tasks.py`/`settings.py` (edição coordenada: T-04 adiciona crons de cobrança, T-05 adiciona `release_escrow` — funções distintas; se houver conflito de merge, T-05 após T-04)
- **Wave 5:** T-06 (split+fees+estorno+wiring criação+circuit breaker) — depende T-04+T-05; T-08 (webhooks) — depende T-04+T-05
- **Wave 6 (frontend — `parallel-hint: back-front` candidato):** T-10 (serviços+tela 16 shell) — depende do contrato de endpoints (T-06). **Os componentes de UI podem começar contra o Stub/contrato assim que T-06 fixar os schemas**, em paralelo ao restante do backend (T-08/T-09), reduzindo o caminho crítico.
- **Wave 7:** T-11 (checkout cartão/PIX) — depende T-10
- **Wave 8:** T-12 (upgrade/downgrade + nova-entrega F-03 E3 + stories) — depende T-11
- **Wave 9:** T-13 (checkpoint Safe2Pay contrato — DEC-003) — depende T-06+T-08

> **parallel-hint (back-front):** SINALIZADO. A partir do momento em que T-06 fixa os schemas de `POST /v1/payments/assinar` / `POST /v1/deliveries` (card/pix) / `GET /v1/payments/chave-publica`, a trilha frontend (T-10→T-11→T-12) roda em paralelo à trilha backend remanescente (T-08 webhooks, T-09 conciliação), pois consomem o **Stub/contrato** e não os internals. Ownership de arquivo é disjunto (apps/web vs apps/api), permitindo dois executores.

> **Squad-review pós-execute:** ROADMAP recomenda `squad-review` após o execute desta phase (integration + dinheiro real). Acionar antes de `/gsd:verify-work 10`.

---

## Reconciliation expectations

`/gsd:reconcile-state 10` verifica:
- Todos os arquivos de `files_modified` existem; os 3 modelos novos + colunas de assinatura presentes na migration 0009
- Endpoints declarados têm handler (`chave-publica`, `assinar`, cobrança/estorno, `webhooks/safe2pay`)
- Skills citadas de fato aplicadas: `_call_safe2pay` checa `HasError`; webhook usa `compare_digest`; split tem invariante de soma; release_escrow usa aware-UTC; cartão cifrado no cliente; zero `#hex` no frontend
- Nenhum cartão/token/segredo em log (grep); nenhum `[ASSUMIDO]` sem TD correspondente
- Nenhum arquivo-fantasma; nenhuma feature fantasma

---

## Rollback plan

- Revert dos commits `feat(phase-10/...)` por wave
- `alembic downgrade -1` (migration 0009 é reversível — testado no CI)
- Feature flag de pagamento online OFF: criação de entrega volta a só `direct` (coexistência Phase 7-9 intacta); assinatura recorrente desligada (lojistas em trial não cobrados)
- Rotacionar `SAFE2PAY_TOKEN_ENCRYPT_KEY`/`RSA_PRIVATE_KEY` se houver suspeita de exposição (não basta remover do histórico)

---

## Plan-checker report

{Preenchido automaticamente pelo gsd-plan-checker}

- Status: {PASS | FLAG | BLOCK}
- Skills coverage: {X/Y obrigatórias citadas}
- Threat model: presente (TH-A..TH-M)
- Performance budget: presente
- Observability checklist: presente
- Integration contracts: presente (validados por Stub — Gate 5)
- Revision iteration: 1
