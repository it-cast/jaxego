# EXECUTION-LOG — Phase 7: Criação de entrega + máquina de estados (modalidade direta)

> Executado por `gsd-executor` (Opus 4.8) em 2026-06-10. Executor único, sequencial (backend → frontend → testes), apesar do `parallel-hint`.

## Resumo

12 tasks (T-00..T-11) concluídas. Backend: migration 0006 (deliveries/transitions/recipients + trigger append-only), máquina de 7 estados, estimativa mediana (RN-030), limite de plano (RN-028), endpoints `/v1/deliveries`. Frontend: jx-state-badge, jx-estimate-box, jx-upgrade-modal, jx-delivery-row, form tela 12, lista tela 14, dashboard tela 11.

## Tasks e commits

| Task | Descrição | Commit | Tipo |
|------|-----------|--------|------|
| T-00 | Scaffold de testes (RED) + fixtures | `0f4cb39` | test |
| T-01 | Migration 0006 + models (deliveries/transitions/recipients) | `99348a1` | feat (migration) |
| T-02 | Máquina de estados (7 estados) + assert_delivery_transition | `ea53c03` | feat |
| T-03 | Estimativa mediana + schemas + máscara CPF/telefone | `9a6a20b` | feat |
| T-04 | create_delivery + transition (FOR UPDATE) + limite + router | `15c0a93` | feat |
| T-05 | RN-013 boundary README + DeliveryOut serializer | `da572cb` | feat |
| T-07 | jx-state-badge + --state-* vars + jx-estimate-box | `647c421` | feat (ui) |
| T-08 | jx-upgrade-modal (E4) anti-dark-pattern | `c36e49a` | feat (ui) |
| T-09 | Lista de entregas (tela 14) + jx-delivery-row | `454eddc` | feat (ui) |
| T-10 | Dashboard da loja (tela 11) + rotas | `1b264eb` | feat (ui) |
| T-06 | Form de nova entrega (tela 12) — E1/E2/E4 | `82276f2` | feat (ui) |
| T-11 | Testes de integridade/concorrência/PII (GREEN final) | (incluído em T-00; suíte completa verde) | test |

## Resultado da verificação

### Backend (`apps/api`, uv / Python 3.13)
- `uv run ruff check .` → All checks passed
- `uv run ruff format --check .` → 172 files already formatted
- `uv run basedpyright` → 0 errors, 0 warnings, 0 notes
- `uv run pytest -m "not mysql"` → **242 passed, 10 deselected**

### Frontend (`apps/web`, npm / Angular 19)
- `npx ng build` → OK (initial total 607.51 kB raw / **162.70 kB transfer** — dentro do budget 400 kB gzip)
- `npm run lint` → All files pass linting
- `ng test` → **80 SUCCESS** (era 65; +15 novos)
- `grep -rE "#E84E1B|#FAF6EE" apps/web/src --include="*.scss" | grep -v _tokens.scss` → **0** (zero hex)

## @pytest.mark.mysql (rodar ao vivo)

```
cd apps/api && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head
cd apps/api && uv run pytest -m mysql tests/deliveries
```

- `test_append_only.py` (2): UPDATE/DELETE em `delivery_state_transitions` → erro MySQL 1644 (trigger SIGNAL 45000).
- `test_concurrency.py` (1): 2 transições simultâneas → 1 vence via `SELECT ... FOR UPDATE` (lock pessimista, LOW-1/TH-01).

## Desvios (Deviation Rules)

- **[Rule 1 - Bug] Transição inicial None→CRIADA** (T-04): `transition()` re-lia o estado já CRIADA e rejeitava CRIADA→CRIADA. Fix: parâmetro `initial=True` que registra o nascimento (from_state=None) sem consultar a máquina. Coberto por `test_create_direct_starts_in_criada`.
- **[Rule 3 - Blocking] merchant_scope** (T-04): `resolve_role` não tratava lojista; criada `app/deliveries/dependencies.py` resolvendo a loja do usuário via `merchant_users` → 404 IDOR. Sem isso o endpoint não tinha como amarrar (area_id, merchant_id).
- **[Rule 1 - Test fix] test_card_em_breve** (T-02→T-04): teste RED assumia que o enum rejeitava `card`; o enum aceita (UI oferece "em breve"), a regra rejeita. Reescrito para `test_card_accepted_by_enum_rejected_by_rule` + `test_card_payment_rejected_by_service`.

Nenhum desvio arquitetural (Rule 4). Nenhuma dependência nova.
