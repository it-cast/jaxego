# EXECUTION-LOG — Phase 10: Safe2Pay núcleo (assinaturas, cobrança com split, escrow, estornos)

> Executado por gsd-executor em 2026-06-11. ⚠ DINHEIRO REAL. Tudo Safe2Pay atrás do
> `PaymentPort` + Stub (D-09) — testes NUNCA tocam Safe2Pay real/sandbox.
> **PAUSADO no T-13** (checkpoint:human-action — confirmação do contrato Safe2Pay).

## Resultado dos gates locais

**Backend (`apps/api`, uv/Python 3.13):**
- `uv run ruff check .` → All checks passed
- `uv run ruff format --check .` → 281 files already formatted
- `uv run basedpyright app/` → 0 errors, 0 warnings, 0 notes
- `uv run pytest -m "not mysql"` → **370 passed, 18 deselected** (baseline era 326 → +44 testes)
- Naive-datetime guard (TD-010) cobre `app/payments/*` → OK (sem violação)

**Frontend (`apps/web`, npm/Angular 19):**
- `npx ng build` → Application bundle generation complete (só warning pré-existente maplibre)
- `npm test` (ng test) → **121 SUCCESS**
- `npm run lint` (ng lint) → All files pass linting
- `grep -rE "#E84E1B|#FAF6EE" src --include="*.scss" | grep -v _tokens.scss` → **0** (Gate 2)

## Tasks concluídas (commit por task, direto em master)

| Task | Commit | Descrição |
|------|--------|-----------|
| T-00 | 71ef0db | scaffold testes + Stub fixture + RED skeleton + naive lint |
| T-01 | a8425c7 | cripto AES-GCM/RSA-OAEP + models + migration 0009 + config/env |
| T-02 | 32e9ebe | PaymentPort + Safe2PayHttpAdapter (HasError) + Stub + factory |
| T-03 | 4554b01 | repo + service base + schemas (idempotência) |
| T-04 | 888e295 | assinatura recorrente + cron cobrança + inadimplência + upgrade/downgrade |
| T-05 | ad97620 | escrow interno 24h (hold/release/freeze + cron) |
| T-06 | 97e70a9 | cobrança split + fees + estorno + wiring card/pix + circuit breaker |
| T-07 | 6890330 | subconta do entregador (gancho MEI aprovado) |
| T-08 | 7d18356 | webhooks idempotentes (log→HMAC→dedup→fila→200) + defesa em profundidade |
| T-09 | 8421a5d | conciliação diária extrato × platform_charges → alerta >R$0,01 |
| T-10 | 604263c | frontend serviços billing/cripto + tela 16 status + histórico |
| T-11 | 52a18ff | checkout cartão (RSA no cliente) + PIX QR + method toggle |
| T-12 | 08b8681 | upgrade/downgrade + nova-entrega card/pix ativo (F-03 E3) + stories |
| T-13 | — | **CHECKPOINT (human-action)** — confirmar contrato Safe2Pay (DEC-003) |

## Decisões-chave aplicadas

- **Cripto AES-256-GCM (Python lib `cryptography`):** formato `base64(nonce12 + ct_com_tag)`
  — NÃO o layout Node `iv+tag+ct` (Pitfall 1). `InvalidTag` → `RuntimeError` (NUNCA retorna
  o blob — fallback texto-puro do Node deliberadamente NÃO portado). RSA-OAEP-2048 SHA-256.
- **PaymentPort (ADR-009 v2):** Protocol + `Safe2PayHttpAdapter` (`_call_safe2pay` SEMPRE
  checa `HasError`, 3 subdomínios, SSRF guard) + `PaymentStubAdapter`. Testes só Stub.
- **Split:** `amount==Σsplits` em centavos inteiros; residual→Jaxegô. No CRIADA (sem
  courier ainda) → 1 leg p/ Jaxegô; corrida vai ao escrow interno, split no payout (Phase 11).
- **Escrow 24h:** release só FINALIZADA+24h aware-UTC sem disputa, atômico + idempotente.
- **Webhooks:** idempotência UNIQUE(tx,status), HMAC `compare_digest`, NUNCA 500, NUNCA
  libera dinheiro só pelo webhook.
- **Migration 0009:** reversível, revision id 28 chars (≤32), sem drop_index redundante.

## Desvios (deviation rules)

- **[Rule 1 — Bug] Teste HasError exercitava DNS real:** o `assert_safe_url` resolve DNS;
  o teste de `HasError` usava host `.example` (falha de resolução). Isolei o HasError-check
  com monkeypatch de `assert_safe_url` (o SSRF tem teste próprio com IP literal 169.254...).
- **[Rule 1 — Behavior change] Teste Phase-7 `test_card_payment_returns_422`:** Phase 10
  ativa card/pix (REQ-034). Atualizei p/ `test_card_payment_now_active` (201/CRIADA).
- **[Rule 2 — Missing critical] Guard de assinatura ativa** adicionado em `create_delivery`
  (SAAS-BILLING §9): blocked/cancelado bloqueia criação.
- **[Rule 3 — Blocking] jx-field sem `(blur)` Output:** adicionei `@Output() blurred`
  (não-quebra) para a validação inline do `jx-card-form`.
- **[Rule 1 — Lint] `@Output() encrypted` colidia com evento DOM nativo** → renomeado
  `cardEncrypted`.

## Itens @pytest.mark.mysql (RODAR AO VIVO contra MySQL 8)

```bash
cd apps/api && uv run pytest -m mysql tests/db/test_migration_0009.py
```
- `test_migration_0009.py` — migration 0009 reversível ao vivo (upgrade→downgrade→upgrade):
  cria/dropa `platform_charges`/`escrow_ledger`/`payment_webhook_events` +
  `merchant_subscriptions.billing_status/safe2pay_token` + `couriers.s2p_recipient_id`;
  prova `downgrade` simétrico sem errno 1553. Os demais testes de cobrança/escrow/split/
  webhook rodam em SQLite (Stub) e já passam em `-m "not mysql"`.

> Alinhar fixtures @mysql a `settings.database_url` (test_migration_0009 usa o pattern da
> 0008, já alinhado — NÃO usa TEST_MYSQL_URL:3306, lição Phase 7).

## T-13 — o que o checkpoint precisa do humano

Ver bloco "CHECKPOINT REACHED" na devolução ao orquestrador. Resumo: confirmar com o
contrato/Postman Safe2Pay real as suposições A1/A2/A4/A9 (split disponível+formato, HMAC
nativo de webhook, endpoints de estorno) e A3 (subconta via API). Cada divergência → ADR
que supera DEC-003, ajustando APENAS o `safe2pay_adapter.py`. Até lá: produção bloqueada
(TD-10-01/03 `pre_launch_blocker`), dev/test 100% no Stub.
