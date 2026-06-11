# EXECUTION-LOG — Phase 8: Despacho em cascata + oferta + aceite

> Executado por gsd-executor em 2026-06-10 (executor único, sequencial: backend → frontend → testes).
> Commits diretos em `master`. Janela de execução: ~1 sessão.

## Resumo

12 tasks (T-01..T-12) concluídas em 12 commits atômicos. Backend (T-01..T-08 + T-02 testes) + frontend (T-09..T-12). Gate 7 verde local; teste de corrida do aceite e migration 0007 marcados `@pytest.mark.mysql` para verificação ao vivo.

## Tasks concluídas (ordem das waves)

| Task | Commit | Descrição |
|------|--------|-----------|
| T-09 | `e4cfec2` | 5 vars `--score-*` em `_semantic.scss` (claro+dark) derivadas de `color.score_level` |
| T-01 | `11d148f` | Migration 0007 `merchant_courier_favorites`/`_blocks` (RN-014) + models |
| T-05 | `dd42ffa` | Adapters OSRM (`RoutingPort`) + push VAPID (`PushPort`) + Stub + fallback haversine + `rank_key` |
| T-03 | `caf7a6f` | `OfferOut` (RN-013) + `offer_state.py` Redis (ADR-104) + exceptions + `core/redis.py` + `dispatch/dependencies.py` |
| T-04 | `c2dfe70` | Aceite único (Lock + FOR UPDATE + máquina idempotente) + GET active + decline |
| T-06 | `ab971a8` | Cascata: `build_candidates` (favoritos→ranking, exclui bloqueados) + `dispatch_offer_task` re-enfileirável |
| T-07 | `11c9547` | `send_push_task` + fila + payload sem PII (LOW-5) + E4 (cancel CRIADA → cancel_pending_offers) + `.env.example` |
| T-08 | `985246f` | CRUD favoritos/bloqueados da loja (`/v1/merchants/dispatch/*`) |
| T-02 | `b5e32ea` | Suíte de testes: corrida(@mysql) + privacidade + elegibilidade + TTL + cascata + cancel + push/routing |
| T-10 | `22691cd` | App entregador home (tela 04) + `jx-score-chip` + `jx-accepted-courier-card` |
| T-11 | `af78beb` | `jx-offer-sheet` + `jx-offer-timer` (tela 05) + `offer.service` |
| T-12 | `c6407ec` | Loja favoritos/bloqueados (tela 15) + `jx-favorite-row` / `jx-blocked-row` |

## Decisões-chave implementadas

- **Aceite único (defesa em 3 camadas):** autorização courier-alvo da `offer:{id}` → 404 `NotOfferTargetError` (não 403); redis `Lock(blocking_timeout=2)` com release token-checked (`Lock.release()`, nunca DEL); `SELECT ... FOR UPDATE` (reuso `transition()` Phase 7) + transição idempotente CRIADA→ACEITA. 2º aceite → 409 `OfferAlreadyTakenError` **sem penalidade** (F-05 E3 — 0 transição CANCELADA, 0 transição ACEITA extra).
- **Cascata sequencial (RN-009):** `dispatch_offer_task` arq re-enfileirável (`_defer_by=timeout_oferta_s+ε`), estado em Redis `offer:{id}` (TTL = config da área) + `dispatch:{id}:candidates`; avanço idempotente compare-and-advance + lock `cascade:{id}` (Pitfall 3). Favoritos por `priority` → ranking `rank_key`. Bloqueado nunca candidato (set-difference antes).
- **Redis TTL fonte de verdade do timer (ADR-104):** `jx-offer-timer` cosmético; re-sync ao servidor; nunca decide expiração no cliente.
- **RN-013:** `OfferOut` separado SEM `dropoff_address`/`number`/`complement` por construção; só bairro + distância. Verificado no schema E no payload E na UI (sheet nunca renderiza rua/número).
- **Adapters degradam:** OSRM → haversine ×1.4 + `eta_degraded`, nunca raise (TH-8); SSRF allowlist (TH-9). Push VAPID lazy import + payload sem PII (LOW-5) + degrade silencioso. Secrets via env (Gate 8).
- **KPI norte:** evento `dispatch.offer.accepted` com `elapsed_ms` (criação→aceite), sem PII.

## Desvios (deviation rules)

- **[Rule 1 — Bug] `service.py` KPI elapsed_ms naive-vs-aware:** ao calcular `accepted_at - created_at`, o `created_at` lido do SQLite vem naive enquanto `accepted_at` é aware → `TypeError`. Corrigido com `ensure_aware_utc()` nos dois (read-boundary TD-010). Pego pelo teste `test_accept`. Commit `b5e32ea`.

Nenhum desvio Rule 2/3/4. Sem checkpoints (plano autônomo).

## Verificação local (Gate 7)

**Backend** (`apps/api`):
- `uv run ruff check .` → All checks passed
- `uv run ruff format --check .` → 200 files already formatted
- `uv run basedpyright` → 0 errors, 0 warnings
- `uv run pytest -m "not mysql"` → **265 passed, 11 deselected**
- Guard naive-datetime (TD-010) cobre `dispatch/` → verde (zero `datetime.utcnow()`)
- `uv add pywebpush` (runtime) + `uv add --group dev fakeredis`; `uv.lock` regenerado

**Frontend** (`apps/web`):
- `npm run lint` → All files pass linting
- `npx ng build` → OK (initial total **162.73 kB gzip** < 400 budget)
- `npx ng test` → **104 passed** (+39 novos)
- `grep -rE "#E84E1B|#FAF6EE" src --include="*.scss" | grep -v _tokens.scss` → **0**

**Integration contracts (Gate 5):** OSRM (`duration`/`distance`) e push VAPID validados contra Stub em `tests/integrations/test_routing.py` + `test_push.py`.

## Itens `@pytest.mark.mysql` (verificação ao vivo — MySQL 8 + Redis reais)

```bash
# 1. Migration 0007 reversível (upgrade + downgrade -1)
cd apps/api && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head

# 2. TESTE DE CORRIDA do aceite (critério nº 1) — 2 aceites simultâneos → 1 vence, 1 → 409 sem penalidade
cd apps/api && uv run pytest -m mysql tests/dispatch/test_accept_race.py -x

# 3. Suíte mysql completa (inclui concorrência Phase 7 + spatial Phase 6)
cd apps/api && uv run pytest -m mysql
```

## O que o humano verifica ao vivo

1. **Migration 0007** aplica + reverte; tabelas `merchant_courier_favorites`/`_blocks` com UNIQUE(area,merchant,courier) + FK RESTRICT + índice (area,merchant).
2. **Corrida do aceite (1 vencedor):** `test_accept_race.py` — exatamente 1 ACEITA, 1 → 409 `OfferAlreadyTakenError`, `cancelled_at` nulo (sem penalidade).
3. **RN-013 payload:** o courier nunca recebe endereço completo do destino (smoke do sheet tela 05 + `test_offer_privacy.py` já verde no not-mysql).

## Pendências / notas

- `send_push_task` envia para subscription vazia no M1 (não há tabela `push_subscriptions` — Phase 9). Stub valida o shape sem PII; o VAPID real degrada silencioso sem subscription.
- Score no `jx-score-chip` é placeholder (`probation`) até o endpoint de scoring (ADR-013 — M1 exibe, não pondera). Documentado em `## Known Stubs` do SUMMARY.
- TD-12-01 (Web Push VAPID vs FCM no APK) registrada como `post_launch_30d` — contrato `PushPort` isola a troca.
