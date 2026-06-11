# RECONCILIATION — Phase 8: Despacho em cascata + oferta + aceite

**Data:** 2026-06-10
**Método:** PLAN/UI-SPEC/RESEARCH (prometido) × código real + verificação ao vivo contra MySQL 8 + Redis

---

## Prometido vs. Entregue

| Área | Prometido | Real | Status |
|---|---|---|---|
| Favoritos/bloqueados (migration 0007) | merchant_courier_favorites + _blocks separados (RN-014) | `0007_dispatch_favorites_blocks` | ✅ **aplica + reversível ao vivo** |
| Cascata (RN-009, nunca broadcast) | favoritos→auto sequencial, arq job re-enfileirável, Redis offer state | dispatch_offer_task + build_candidates | ✅ |
| Aceite único (peça crítica) | autorização → Redis Lock → FOR UPDATE → transição idempotente; 2º → rejeição sem penalidade | accept_offer 3 camadas | ✅ **verificado ao vivo: 10/10 stress, sempre 1 vencedor** |
| Timer Redis TTL (ADR-104) | TTL fonte de verdade, cronômetro cosmético | offer_state.py | ✅ |
| Privacidade destino (RN-013) | oferta só bairro+distância, nunca endereço completo | OfferOut | ✅ (test_offer_privacy verde) |
| Localização entregador (ADR-007) | nunca exposta à loja | — | ✅ |
| Ranking | OSRM ETA + score placeholder + carga + preço | rank_key | ✅ |
| Adapters | OSRM (Stub + haversine×1.4 eta_degraded) + push VAPID (Stub, sem PII) | RoutingPort/PushPort | ✅ (Gate 5 stub) |
| Frontend | home tela 04, jx-offer-sheet + jx-offer-timer (motion+a11y), favoritos tela 15, jx-score-chip (--score-*) | implementado | ✅ |

---

## Verificação ao vivo (MySQL 8 + Redis real)
| Check | Resultado |
|---|---|
| `alembic upgrade head` (0001→0007) | ✅ aplica |
| Reversibilidade 0007 (downgrade explícito → upgrade) | ✅ (sem bug 1553 — executor aprendeu da 0006) |
| **Aceite concorrente (2 simultâneos)** | ✅ **10/10 runs: exatamente 1 ACEITA, 1 rejeitado sem penalidade (cancelled_at NULL), 1 transição CRIADA→ACEITA** |
| `pytest -m mysql tests/dispatch` (3 runs) | ✅ verde |
| `pytest -m "not mysql"` | ✅ 265 passed |
| Frontend (ng build/lint/test) | ✅ 162.73 kB gzip, lint limpo, 104 testes, zero hardcode |

---

## Bugs pegos no smoke ao vivo
1. **Bug de teste (race):** o teste de corrida assertava um tipo de exceção específico (409) para o perdedor, mas dependendo do timing o perdedor cai em qualquer das 3 camadas (404 NotOfferTarget / 409 AlreadyTaken / InvalidTransition) — todas "sem penalidade". → Corrigido (`68fff82`): teste assevera a INVARIANTE real (exatamente 1 vencedor, 0 penalidade, qualquer rejeição válida). Produção INALTERADA (10/10 stress confirma sem dupla-aceitação).
2. **Bug naive-vs-aware (KPI):** `elapsed_ms` subtraía created_at naive (SQLite) de accepted_at aware → TypeError. Corrigido com ensure_aware_utc (pego pelo test_accept).
3. **Format:** ruff format nos adapters (chore b0904b3).

## Critérios de aceite do ROADMAP
| Critério | Resultado |
|---|---|
| 2 aceites simultâneos → lock garante 1 vencedor (F-05 E3) | ✅ verificado ao vivo (10/10) |
| Payload de oferta sem endereço completo do destino (RN-013) | ✅ |
| Redis TTL fonte de verdade do timer (ADR-104) | ✅ |
| Bloqueado nunca recebe oferta (RN-014) | ✅ |
| Wireframe-contract 05, 04, 15 | ✅ |

## Gates
| Gate | Status |
|---|---|
| Gate 2 (UI-SPEC) | ✅ zero token novo (--score-* derivadas) |
| Gate 3 (Skills) | ✅ PASS após +visual-regression/ionic/responsive (BLOCK→PASS) |
| Gate 4 (Security Baseline) | ✅ 10 ameaças → threat model |
| Gate 5 (Integration) | ✅ OSRM/push validados por Stub |
| Gate 6 (Reconciliation) | ✅ este documento |
| Gate 7 (tests+lint) | ✅ 265+1 backend, 104 frontend, ruff/pyright/ng lint limpos |
| Gate 8 (senior-quality-bar) | ✅ aceite único sem dupla-aceitação, IDOR 404, PII fora de log/push, sem segredo no repo |

## Pendências / follow-up (não-bloqueantes)
- TD-12-01 (Web Push VAPID vs FCM no APK Capacitor) — post_launch_30d.
- push_subscriptions table é Phase 9 (send_push_task com subscription vazia por ora).
- score chip placeholder (probation) até scoring da Phase 13 (ADR-013).
- OSRM real (contrato) validado por Stub; round-trip real quando houver OSRM self-hosted.
