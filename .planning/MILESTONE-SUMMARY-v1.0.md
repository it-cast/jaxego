# Milestone Summary — Jaxegô v1.0 (piloto Pádua)

**Fechado:** 2026-06-12 (autopilot) · **Status:** 15 phases / 14 distintas (sem 11) completas em
dev/test · **Deploy:** gated pelo RELEASE-CHECKLIST (contrato Safe2Pay + verificação ao vivo).

## O que é o Jaxegô
Malha de entregadores por área para o interior do Brasil, integrada ao Menu Certo, com **pagamento
direto** como modalidade de 1ª classe. Multi-área (app única, shared DB, `area_id` em tudo).

## Milestones (todos dev/test ✅)
| MS | Nome | Phases | Entregue |
|----|------|--------|----------|
| MS-01 | Foundation | 1–3 | Infra Docker/CI, multi-área+auth (JWT+TOTP+RBAC), shell Angular/Ionic + design tokens |
| MS-02 | Cadastros & malha | 4–6 | Cadastro de loja (Free/Receita), KYC entregador 2 níveis + docs B2, área operável (bairros/cobertura/frete) |
| MS-03 | Core de entregas | 7–9 | Máquina de 7 estados, despacho em cascata + aceite, comprovação foto+GPS, tracking público + mapa, notificações |
| MS-04 | Financeiro checkout & integrações | 10, 12 | Safe2Pay núcleo (cartão/PIX split + escrow + estornos), API pública idempotente + webhooks HMAC (Menu Certo) |
| MS-05 | Operação & release piloto | 13–14 | Governança (score/avaliações/suspensão), admin plataforma, jobs LGPD, infra LLM, hardening + CI release + APK |
| MS-06 | Pós-piloto financeiro | 15 | Fatura mensal + bloqueio, disputa financeira (90d), saques, conciliação diária |

## Decisão estruturante desta sessão
**DEC-004 (resequenciamento):** a parte financeira pesada de Safe2Pay (ex-Phase 11: fatura/disputas-
resolução/saques/conciliação) foi movida para **depois do deploy** → Phase 15 (MS-06), a última. Ordem
de build: 12 → 13 → 14 (deploy) → 15. Phase 13 religada a [9]. No deploy ficam live assinatura + cartão/
PIX (Phase 10), **assumindo contrato Safe2Pay assinado**.

## Números (dev/test)
- **14 phases distintas** completas; ~494 testes backend (not-mysql) + 204 frontend.
- **13 migrations** (0001–0013), reversíveis (testes `@mysql` escritos).
- **Zero hex** hardcoded no frontend (3 exceções técnicas documentadas).
- Gates 2–8 verdes em todas as phases; **zero FAIL-BLOCK** do Senior Quality Bar.

## Phases desta sessão de autopilot (12–15)
- **12** API pública: API key por área (argon2id), POST idempotente 24h, webhooks outbound HMAC + retry 8×, tela 22.
- **13** Governança: score explicável (peso 0 no M1 — ADR-013), avaliações, suspensão/recurso + reversão SLA, admin plataforma cross-área auditado.
- **14** Hardening: jobs LGPD (anonimização 12m + exclusão 30d), infra LLM (router + ai_usage_log, sem feature), refino ETA, CI release + APK debug, RELEASE-CHECKLIST.
- **15** Financeiro back-office: fatura + bloqueio F-03 E5, disputa financeira, saques (payout), conciliação.

## Bloqueadores de deploy (RELEASE-CHECKLIST)
1. 🔴 **Contrato Safe2Pay** (TD-10-01..04, TD-15-01) — habilita cartão/PIX + back-office financeiro em produção.
2. 🔴 Secrets de produção · migrations em staging (`pytest -m mysql`) · seed admin de plataforma.
3. 🟡 Revenue share % (TD-13-01), path da API pública c/ Menu Certo (TD-12-01), Lighthouse/p95 reais (TD-14-03), APK assinado (TD-14-04).

## Próximos passos
1. Resolver os BLOCKERS do `RELEASE-CHECKLIST.md` (contrato, secrets, migrations, seed admin).
2. Rodar `pytest -m mysql` (migrations 0004–0013) contra MySQL real (staging).
3. Configurar GitHub remote + validar CI remoto; gerar APK assinado para UAT em device.
4. Preencher os qualitativos das retros (`.planning/retros/`).
5. Deploy do piloto Pádua (pagamento direto live; cartão/PIX quando o contrato fechar).
