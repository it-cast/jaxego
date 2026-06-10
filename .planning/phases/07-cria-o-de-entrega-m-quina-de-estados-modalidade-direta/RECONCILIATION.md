# RECONCILIATION — Phase 7: Criação de entrega + máquina de estados (modalidade direta)

**Data:** 2026-06-10
**Método:** PLAN/UI-SPEC/RESEARCH (prometido) × código real + verificação ao vivo contra MySQL 8

---

## Prometido vs. Entregue

| Área | Prometido | Real | Status |
|---|---|---|---|
| Entidades | deliveries, delivery_state_transitions (append-only), recipients (migration 0006) | `0006_deliveries` | ✅ **aplica + reversível ao vivo** |
| Máquina de 7 estados (RN-019) | transições válidas completas; inválida → 422; transição via máquina | DELIVERY_TRANSITIONS + assert_delivery_transition + transition() | ✅ (testes exaustivos) |
| Histórico append-only (RN-012) | trigger MySQL nega UPDATE/DELETE em delivery_state_transitions (SIGNAL 45000) | trg_dst_no_update/no_delete | ✅ **verificado ao vivo: errno 1644** |
| Concorrência | SELECT FOR UPDATE (lock pessimista) — 1 vence | transition() com FOR UPDATE | ✅ **verificado ao vivo: 1 wins, 1→invalid** |
| Criação F-03 (direta) | modalidade direta só; card/PIX "em breve" | create_delivery | ✅ |
| Estimativa mediana (RN-030) | mediana das tabelas elegíveis (reuso Phase 6) | preço efetivo por trecho | ✅ |
| Limite de plano (RN-028) | COUNT server-side, Free 2/mês, CANCELADA não conta, 3ª→402 | implementado | ✅ |
| Recipients | hash CPF nunca puro | cpf_hash | ✅ |
| RN-013 | endereço completo do destino não exposto ao entregador (separação p/ Phase 8) | boundary serializer | ✅ |
| Frontend | jx-state-badge (7 estados via color.delivery_state), jx-estimate-box, jx-upgrade-modal, lista tela 14, dashboard tela 11, form tela 12 | implementado | ✅ |
| IDOR | merchant só suas entregas (merchant_scope 404) | implementado | ✅ |

---

## Verificação ao vivo (MySQL 8 real)
| Check | Resultado |
|---|---|
| `alembic upgrade head` (0001→0006) | ✅ aplica |
| Reversibilidade 0006 (downgrade→upgrade 2×) | ✅ após fix `dcd940a` |
| Triggers delivery_state_transitions | ✅ trg_dst_no_update/no_delete |
| `pytest -m mysql tests/deliveries` | ✅ 3 passed (append-only errno 1644 + concorrência FOR UPDATE) |
| `pytest -m "not mysql"` | ✅ 242 passed |
| Frontend (ng build/lint/test) | ✅ 162.70 kB gzip, lint limpo, 80 testes, zero hardcode |

---

## Bugs reais pegos no smoke ao vivo (valor da verificação)
1. **Bug de teste (seed/URL):** os testes @mysql de delivery faziam INSERT cru omitindo colunas NOT NULL (`pickup_address` → errno 1364) e usavam `TEST_MYSQL_URL` default 3306 (colidia com MySQL local). → Corrigido (`1785f33`): seed via ORM + `settings.database_url`/NullPool. Também expôs um snapshot REPEATABLE READ mascarando o lock no teste de concorrência (corrigido para asserção determinística).
2. **Bug de migration (real):** `downgrade()` da 0006 falhava com errno 1553 (drop de índice necessário a FK antes de dropar a tabela). → Corrigido (`dcd940a`): removidos os drop_index redundantes; drop_table em ordem de FK. Reversibilidade importa para rollback de produção.

## Critérios de aceite do ROADMAP
| Critério | Resultado |
|---|---|
| Transições inválidas → 422 (exaustivo) | ✅ |
| UPDATE/DELETE em delivery_state_transitions → erro MySQL | ✅ errno 1644 ao vivo |
| F-03 E1/E2/E4 | ✅ |
| Wireframe-contract 12, 11, 14 | ✅ |
| IDOR merchant 404 | ✅ |

## Desvios
1. Rule 1: transição inicial None→CRIADA (`initial=True`).
2. Rule 3: `merchant_scope` criado (resolve_role não tratava lojista) → IDOR 404.
3. Rule 1: test_card_em_breve reescrito (enum aceita; regra no serviço).

## Gates
| Gate | Status |
|---|---|
| Gate 2 (UI-SPEC) | ✅ zero token novo (vars --state-* derivadas) |
| Gate 3 (Skills) | ✅ PASS (19/19, 1ª iteração) |
| Gate 4 (Security Baseline) | ✅ 8 ameaças → threat model |
| Gate 5 (Integration) | N/A (integration_check:false) |
| Gate 6 (Reconciliation) | ✅ este documento |
| Gate 7 (tests+lint) | ✅ 242+3 backend, 80 frontend, ruff/pyright/ng lint limpos |
| Gate 8 (senior-quality-bar) | ✅ máquina server-side, IDOR 404, sem N+1, PII fora de log, dinheiro em centavos |

## Pendências / follow-up (não-bloqueantes)
- public_token ULID reservado p/ tracking público (Phase 9).
- Estados ACEITA+ só serão exercidos nas Phases 8/9 (a máquina inteira já está definida e testada).
- Estimativa mediana é `[ASSUMIDO]` simples (TD-009).
