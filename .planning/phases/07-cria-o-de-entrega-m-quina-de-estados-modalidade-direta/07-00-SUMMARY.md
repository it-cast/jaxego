---
phase: 07-cria-o-de-entrega-m-quina-de-estados-modalidade-direta
plan: 00
subsystem: api
tags: [state-machine, deliveries, append-only-trigger, lgpd, angular, mysql, fastapi]

requires:
  - phase: 02-core-auth-multiarea
    provides: append-only trigger (audit_log), AreaScopedMixin, PII masks, mask_phone/mask_document
  - phase: 04-cadastro-loja
    provides: merchants/merchant_subscriptions/subscription_plans (limite de plano)
  - phase: 05-couriers-kyc
    provides: máquina de estados pattern (couriers/state_machine.py), couriers.is_online/status
  - phase: 06-area-operavel
    provides: elegibilidade espacial (is_eligible, point_in_polygon), catálogo de bairros, tabelas de frete
  - phase: 03-shell-design-system
    provides: jx-field, jx-data-table, jx-plan-card, 4 componentes de estado, máscaras BR, tokens claro/dark
provides:
  - migration 0006 (deliveries, delivery_state_transitions append-only, recipients)
  - máquina de 7 estados (RN-019) com transition() lock pessimista FOR UPDATE
  - estimativa mediana de frete (RN-030) sobre elegibilidade Phase 6
  - limite de plano server-side (RN-028), CANCELADA não conta
  - endpoints /v1/deliveries (POST/GET/{id}/cancel) com IDOR 404
  - jx-state-badge (7 estados), jx-estimate-box, jx-delivery-row, jx-upgrade-modal
  - form nova entrega (tela 12), lista (tela 14), dashboard (tela 11)
affects: [08-despacho-oferta-aceite, 09-comprovacao-execucao, 10-cobranca-online, 11-fatura-mensal]

tech-stack:
  added: []
  patterns:
    - "transition() é o único ponto de escrita de deliveries.state (FOR UPDATE)"
    - "public_token ULID-like via secrets + Crockford base32 (sem dependência nova)"
    - "merchant_scope dependency resolve loja do usuário (merchant_users) → IDOR 404"
    - "--state-* semantic vars derivadas de color.delivery_state (neutral surface + vivid color)"

key-files:
  created:
    - apps/api/alembic/versions/0006_deliveries.py
    - apps/api/app/deliveries/{models,state_machine,estimate,schemas,service,router,dependencies}.py
    - apps/api/app/deliveries/README.md
    - apps/web/src/shared/components/{state-badge,estimate-box,upgrade-modal,delivery-row}/*
    - apps/web/src/features/loja/entregas/{nova-entrega,entregas-list}.page.*
    - apps/web/src/features/loja/dashboard/dashboard.page.*
  modified:
    - apps/api/app/api/v1/router.py
    - apps/api/tests/conftest.py
    - apps/web/src/styles/_semantic.scss
    - apps/web/src/app/app.routes.ts

key-decisions:
  - "Lock pessimista FOR UPDATE na transição (LOW-1) — Redis lock fica para o aceite Phase 8"
  - "COUNT por query exclui CANCELADA (LOW-3) — evita burlar limite com create+cancel"
  - "Mediana sobre preço efetivo por trecho (bairro/km, LOW-2)"
  - "public_token ULID-like opaco reservado agora para tracking Phase 9 (LOW-4)"
  - "Máquina inteira (7 estados) definida agora; só CRIADA/CANCELADA atingíveis"

patterns-established:
  - "Append-only via trigger MySQL SIGNAL 45000 replicado para delivery_state_transitions"
  - "RN-013: endereço completo separado de bairro+distância por construção (Phase 8 offer)"
  - "jx-state-badge é a única fonte do vocabulário visual de estado (texto+ícone+cor)"

requirements-completed: [REQ-021, REQ-022, REQ-023]

duration: ~90min
completed: 2026-06-10
---

# Phase 7 Plan 07-00: Criação de entrega + máquina de estados (modalidade direta) Summary

**Coração transacional do Jaxegô: F-03 cria entrega na modalidade direta nascendo CRIADA, com máquina de 7 estados (RN-019) e histórico append-only via trigger MySQL, estimativa mediana sobre a elegibilidade espacial da Phase 6 e gate de limite de plano server-side.**

## Performance

- **Duration:** ~90 min
- **Started:** 2026-06-10
- **Completed:** 2026-06-10
- **Tasks:** 12/12 (T-00..T-11)
- **Files modified/created:** ~38

## Accomplishments

### Backend (`apps/api`)
- **Migration 0006:** `deliveries` (area-scoped, 7-state, money em centavos inteiros, separação RN-013 do endereço, `public_token` ULID-like unique), `delivery_state_transitions` (append-only, trigger `SIGNAL 45000`), `recipients` (só `cpf_hash`, sem CPF puro). Convenções 0002-0005, FK RESTRICT, índices `(area_id, merchant_id, created_at)` e `(area_id, state)`.
- **Máquina de 7 estados** (`state_machine.py`): `DELIVERY_TRANSITIONS` completa; transição inválida → 422 (testada exaustivamente — produto cartesiano dos 7 estados).
- **`transition()`** (`service.py`): único ponto de escrita de `state`, `SELECT ... FOR UPDATE` (lock pessimista), grava 1 linha append-only com `datetime.now(UTC)` (TD-010).
- **Estimativa mediana** (`estimate.py`): `median_cents` (centavos inteiros), `effective_price_cents` (bairro/km — LOW-2), `eligible_online_prices_cents` reusando `is_eligible` da Phase 6.
- **Limite de plano** (RN-028): `deliveries_this_month` COUNT server-side excluindo CANCELADA; 3ª Free → 402 com payload de upgrade.
- **Endpoints** `/v1/deliveries` (POST/GET/{id}/cancel) com `merchant_scope` (IDOR → 404), rate limit 30/min/loja, telefone mascarado no output, PII fora de log.

### Frontend (`apps/web`)
- **`jx-state-badge`** (7 estados, texto+ícone+cor, variant list/dashboard) + 7 `--state-*` vars derivadas de `color.delivery_state` (claro+dark).
- **`jx-estimate-box`** (faixa/0-entregadores/loading, role=status), **`jx-upgrade-modal`** (E4 anti-dark-pattern, foco preso, Esc), **`jx-delivery-row`** (Cancelar só em CRIADA).
- **Tela 12** (form nova entrega): seções fieldset, máscaras BR, pagamento direto único habilitado, E1/E2/E4.
- **Tela 14** (lista) sobre `jx-data-table` com filtros; **Tela 11** (dashboard) com KPIs mono + "em curso" + H1 italic.

## Verification

- Backend: ruff/format/pyright limpos; **242 pytest not-mysql passed**, 10 deselected (mysql).
- Frontend: ng build OK (162.70 kB gzip), lint limpo, **80 ng test SUCCESS**, **0 hex** hardcoded.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Transição inicial None→CRIADA**
- **Found during:** T-04
- **Issue:** `transition()` relia o estado já CRIADA e rejeitava CRIADA→CRIADA na criação.
- **Fix:** parâmetro `initial=True` registra o nascimento (from_state=None) sem consultar a máquina.
- **Files modified:** apps/api/app/deliveries/service.py
- **Commit:** `15c0a93`

**2. [Rule 3 - Blocking] merchant_scope dependency**
- **Found during:** T-04
- **Issue:** `resolve_role` não tratava lojista; faltava amarrar (area_id, merchant_id) do usuário autenticado.
- **Fix:** `app/deliveries/dependencies.py` resolve a loja via `merchant_users` → 404 IDOR.
- **Commit:** `15c0a93`

**3. [Rule 1 - Test fix] test_card_em_breve**
- **Found during:** T-04
- **Issue:** teste RED assumia que o enum rejeitava `card`; o enum aceita (UI oferece "em breve"), a regra rejeita.
- **Fix:** reescrito como `test_card_accepted_by_enum_rejected_by_rule` + `test_card_payment_rejected_by_service`.
- **Commit:** `15c0a93`

Nenhum desvio arquitetural (Rule 4). Nenhuma dependência nova.

## Known Stubs

- **Bairro no form (tela 12):** o `select` é populado por `GET /v1/neighborhoods` (best-effort); se a loja não tiver endpoint próprio de catálogo, degrada para lista vazia e o backend força E1 no submit. A resolução CEP→bairro do catálogo (Phase 6) é um gancho — o `dropoff_neighborhood_id` é selecionado manualmente. **Intencional nesta phase**; a resolução automática casa com o detalhe de tracking/mapa da Phase 9.
- **Recálculo da estimativa no form:** `jx-estimate-box` recebe a estimativa de volta após o create (não há pré-cálculo via endpoint dedicado nesta phase). A faixa min/max e a taxa por plano vêm da API; a pré-visualização ao vivo antes de submeter é refinamento da Phase 8 (oferta/despacho).

## Itens @pytest.mark.mysql (rodar ao vivo)

```
cd apps/api && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head
cd apps/api && uv run pytest -m mysql tests/deliveries
```

- `test_append_only.py` (2): trigger nega UPDATE/DELETE em `delivery_state_transitions` (errno 1644 / SIGNAL 45000).
- `test_concurrency.py` (1): 2 transições simultâneas serializam via FOR UPDATE (1 vence, 1 → 422).

## Self-Check: PASSED
