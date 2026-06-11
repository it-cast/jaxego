# RECONCILIATION — Phase 10: Safe2Pay núcleo (assinaturas, cobrança com split, escrow, estornos)

**Data:** 2026-06-11
**Método:** PLAN/UI-SPEC/RESEARCH (prometido) × código real + verificação ao vivo (MySQL 8) + Stub (Safe2Pay nunca real)
**⚠ Produção PENDENTE do contrato Safe2Pay (DEC-003 / TD-10-01..04). Dev/test 100% verde com Stub.**

---

## Prometido vs. Entregue

| Área | Prometido | Real | Status |
|---|---|---|---|
| Entidades (migration 0009) | platform_charges, escrow ledger, webhook_events, subconta, campos assinatura recorrente | `0009_safe2pay_billing_escrow` (id 28 chars) | ✅ **aplica + reversível ao vivo** |
| Cripto | AES-256-GCM token cartão + RSA-OAEP-2048 dados cartão (Python cryptography) | `crypto.py` formato `base64(nonce12+ct_com_tag)` | ✅ round-trip + InvalidTag testados |
| PaymentPort (ADR-009 v2) | Protocol + Safe2PayHttpAdapter + Stub | `payments/port.py` + adapter + stub | ✅ (Stub nos testes) |
| Assinatura recorrente | cartão tokenizado + PIX automático + cron + inadimplência 10/20d + guard + upgrade/downgrade | subscriptions + cron arq | ✅ |
| Split por entrega | corrida→subconta escrow, taxa→Jaxegô+revenue share, soma exata centavos | fees.py, wiring criação | ✅ **soma exata testada** |
| Escrow 24h | ledger; release via cron (FINALIZADA+24h sem disputa) | escrow.py | ✅ |
| Estornos (RN-004) | total pré-aceite, parcial 50%/100% | service + adapter | ✅ |
| Subconta entregador | cadastrar no MEI aprovado (RN-010) | couriers/subaccount.py | ✅ (degradação graciosa A3) |
| Webhooks | idempotentes por IdTransaction, log antes, defesa em profundidade (HMAC não confirmado) | webhooks_router | ✅ |
| Conciliação diária | divergência >R$0,01 → alerta | reconcile.py | ✅ |
| Frontend | checkout cartão RSA/PIX QR, status assinatura, upgrade/downgrade, nova-entrega cartão/PIX, 6 componentes | implementado | ✅ |
| Circuit breaker | API fora → cartão/PIX indisponível, direto segue | implementado | ✅ |

---

## Verificação ao vivo (MySQL 8) + Stub
| Check | Resultado |
|---|---|
| `alembic upgrade head` (0001→0009) | ✅ aplica |
| Reversibilidade 0009 (downgrade explícito → upgrade) | ✅ limpo (id 28 chars ≤32; sem 1553) |
| `pytest -m mysql` (incl. migration tests) | ✅ 17 passed (após fix de revisão explícita) |
| `pytest -m "not mysql"` | ✅ 370 passed (cripto, split soma exata, idempotência cobrança+webhook, circuit breaker, inadimplência, estorno — tudo via Stub) |
| Frontend (ng build/lint/test) | ✅ bundle ok, lint limpo, 121 testes, zero hardcode |

---

## Bug pego no smoke ao vivo
- **Testes de reversibilidade de migration frágeis:** usavam `downgrade -1`/`head` relativos → quebram quando uma migration nova é empilhada (test_0008 quebrou ao surgir a 0009). → Corrigido (`48c9f9c`): helper `assert_migration_reversible` com revisões EXPLÍCITAS + restore de head no finally. Também corrigido isolamento pré-existente em test_mysql_constraints (merchants). **Lição:** testes de migration usam revisões explícitas, nunca relativas.
- **Cripto Python (achado do research, evitado):** `AESGCM.encrypt()` anexa a tag ao ciphertext (≠ Node) → formato adaptado; não replicar o layout do SAAS-BILLING (NestJS) cegamente.

## Critérios de aceite do ROADMAP
| Critério | Resultado |
|---|---|
| Recusa de cartão → entrega NÃO criada (F-03 E3) | ✅ |
| Split soma exata + idempotência por Reference/IdTransaction | ✅ |
| Webhook duplicado → processado uma vez | ✅ |
| Circuit breaker: API fora → direto segue | ✅ |
| Escrow: corrida liberada só FINALIZADA+24h sem disputa | ✅ |
| Cripto: cartão nunca em texto puro/log; token AES-GCM; chaves só env | ✅ |

## Gates
| Gate | Status |
|---|---|
| Gate 2 (UI-SPEC) | ✅ zero token novo, checkout seguro |
| Gate 3 (Skills) | ✅ PASS (22/22, ambas leis de billing citadas, 1ª iteração) |
| Gate 4 (Security Baseline) | ✅ 13 ameaças → threat model |
| Gate 5 (Integration) | ✅ contratos Safe2Pay validados por Stub (NUNCA real) |
| Gate 6 (Reconciliation) | ✅ este documento |
| Gate 7 (tests+lint) | ✅ 370+17 backend, 121 frontend, ruff/pyright/ng lint limpos |
| Gate 8 (senior-quality-bar) | ✅ cartão/token/api-key fora de log + só env, idempotência (sem dupla cobrança), split soma exata, IDOR estorno 404 |

## Pendências / follow-up — PRODUÇÃO BLOQUEADA pelo contrato Safe2Pay (DEC-003)
- **TD-10-01 (pre_launch_blocker):** split disponível + shape do payload — confirmar no contrato/Postman.
- **TD-10-03 (pre_launch_blocker):** HMAC de webhook — confirmar se Safe2Pay assina (defesa em profundidade já protege).
- **TD-10-02 (pre_launch_high):** API de subconta do entregador.
- **TD-10-04 (pre_launch_high):** endpoints exatos de estorno (PIX vs cartão).
- Cada divergência → **ADR que supera DEC-003**, ajustando APENAS `safe2pay_adapter.py` (domínio intacto — valor da interface própria ADR-009 v2).
- **Dev/test está 100% funcional e verde com Stub.** O que falta é a confirmação do mundo real para subir produção de cobrança online.
