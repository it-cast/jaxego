# RECONCILIATION — Phase 4: Cadastro e ativação de loja

**Data:** 2026-06-10
**Método:** PLAN.md/UI-SPEC/RESEARCH (prometido) × código real + verificação ao vivo contra MySQL 8

---

## Prometido vs. Entregue

| Área | Prometido | Real | Status |
|---|---|---|---|
| Entidades | merchants, merchant_users, subscription_plans, merchant_subscriptions (migration 0003, reuso de mixins) | migration `0003_merchants_plans` aplicada (0001→0002→0003 em MySQL real) | ✅ |
| Máquina de estados merchant | pending_payment/pending_validation/active/suspended, transições no audit_log | service implementado | ✅ |
| Validação CNPJ/CPF | validate-docbr, dígito + formato + CNPJ alfanumérico jul/2026 | `validate-docbr` 2.0.0, teste alfanumérico | ✅ (LOW-4 resolvido) |
| Receita Federal | adapter Protocol+httpx+Stub, pending_validation no down + job retry 6/6/12/24h | adapter + job arq aware-UTC | ✅ (E1/E4) |
| SMS/SES/geocoding | adapters com stub de dev + SSRF guard | 4 adapters + `assert_safe_url` (allowlist + rejeita IP privado/link-local) | ✅ |
| Anti-enumeração (RN-011) | colisão → mensagem única, tempo ~constante | service reusa padrão da Phase 2 | ✅ (E2) |
| Planos = seeds (DRV-009) | 4 planos como seed editável, Free imutável, só Free ativa | seed; pago → pending_payment | ✅ (E3) |
| Seed idempotente | área Pádua + 4 planos + admin plataforma + admin área, rodar 2x não duplica | `tools/seed.py` | ✅ **verificado ao vivo: 2× → 1 área, 4 planos, 2 users, 1 area_admin** |
| Frontend wizard (tela 02) | stepper, forms BR (CNPJ/CPF/telefone/CEP), persistência sem senha, E1/E2 | `jx-wizard-stepper`/`jx-field`/`jx-plan-card` + cadastro page | ✅ |
| Seleção de plano (tela 16) | cards data-driven do seed, sem dark pattern | implementado | ✅ |
| Estado vazio "Ainda não chegamos aí" | EmptyState + captura email/cidade | implementado | ✅ |
| Banners pending_* + onboarding | warn-banner persistente + hint | implementado | ✅ |
| LGPD | consentimento antes do submit, PII mascarada, fora de log | denylist + máscaras (mask_email/phone/document) | ✅ |

---

## Verificação ao vivo (MySQL 8 real)
| Check | Resultado |
|---|---|
| `alembic upgrade head` (0001→0002→0003) | ✅ aplica limpo |
| Seed idempotente (2×) | ✅ areas=1, subscription_plans=4, users=2, area_admins=1 (sem duplicar) |
| `pytest -m mysql` | ✅ 4 passed (append-only 0002 + UNIQUE composto merchants 0003) |
| `pytest -m "not mysql"` (backend) | ✅ 112 passed |
| Frontend (`ng build`/lint/test) | ✅ 158.62 kB, lint limpo, 33 testes, zero hardcode |

---

## Critérios de aceite do ROADMAP
| Critério | Resultado |
|---|---|
| Testes F-01 E1-E4 | ✅ CNPJ inativo (E1), anti-enumeração (E2), pago→pending_payment (E3), Receita down→pending_validation+job (E4) |
| Wireframe-contract 02-cadastro-loja no UI-SPEC | ✅ |
| Seed idempotente | ✅ verificado ao vivo |
| Zero hardcode (cor + valores de plano) | ✅ grep 0; planos via seed |

---

## Desvios
1. **Rule 3:** `app/core/ratelimit.py` (sliding window in-process) criado para rate limit de signup (threat TH-07) — não havia limiter.
2. **Rule 2:** máscaras de PII (mask_email/phone/document) + `phone`/`document` na denylist de log antecipados (T-03 depende).
3. `.env.example` na raiz (canônico) + cópia em apps/api.

## Gates
| Gate | Status |
|---|---|
| Gate 2 (UI-SPEC) | ✅ zero token novo, reusa Phase 3 |
| Gate 3 (Skills) | ✅ PASS após +trust-safety-ux (FLAG→PASS) |
| Gate 4 (Security Baseline) | ✅ 12 ameaças → threat model → tasks |
| Gate 5 (Integration check) | ✅ contratos dos adapters validados por stub (8 contratos) |
| Gate 6 (Reconciliation) | ✅ este documento |
| Gate 7 (tests+lint) | ✅ 112+4 backend, 33 frontend, ruff/pyright/ng lint limpos |
| Gate 8 (senior-quality-bar) | ✅ sem segredo no repo, PII fora de log, SSRF guard, sem N+1 |

## Pendências / follow-up (não-bloqueantes)
- **Ruído cosmético no `tools/seed.py`:** `Event loop is closed` no teardown asyncio (Windows). Dados corretos; one-shot CLI. Aplicar o mesmo fix de dispose dos testes quando conveniente (baixa prioridade).
- **Smoke de cadastro end-to-end servindo API+frontend** (httpx real contra adapters stub via UI) não rodado; coberto por 112 testes HTTP + 4 mysql. Opcional em /gsd:verify-work 4.
- TD-014 (geocoding público rate limit) e TD-015 (callback SMS assíncrono) registradas (post_launch_quarter).
- Spike de contrato real Receita (minhareceita/BrasilAPI) feito com fixture; validar contra serviço real quando houver ambiente.
