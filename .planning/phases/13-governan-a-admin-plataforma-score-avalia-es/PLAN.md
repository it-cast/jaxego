# Phase 13: Governança — admin plataforma, score, avaliações, suspensão/recurso - PLAN

**Milestone:** MS-05 · **has_ui:** true · **has_pii:** true · **integration_check:** false
**Status:** Ready for execution · **Migration:** 0011 · **Date:** 2026-06-11 (autopilot)
**Depende de:** [9] (DEC-004, primitivo `payment_dispute`)

## Goal
Entregar a governança do piloto: score explicável (snapshot diário, **sem efeito financeiro** —
ADR-013), avaliações pós-entrega, suspensão/recurso com **reversão automática por SLA**, admin de
plataforma cross-área auditado com TOTP, e o shell de disputas/suspensões no admin de área. Resolução
**financeira** de disputa fica na Phase 15 (DEC-004).

## Skills Consultadas
- `owasp-security` (auth-and-session, A01/A03/A07/A09) — fonte do threat model TH-01..TH-08: TOTP no
  admin plataforma (D-06), auditoria de acesso cross-área (TH-02), suspensão auditada append-only
  (TH-03), score sem escrita direta (TH-05). Gate 4 baseline em RESEARCH.md.
- `quality/observability-production` — alerta na reversão automática de SLA (D-05), audit de acesso
  cross-área, métricas de score/disputa; PII fora de log (TH-07).
- `ux-advanced/saas-dashboard-patterns` — telas 23-25 do admin de plataforma (KPIs, listas densas).
- `ux-advanced/data-tables-ux` — todas as listas (áreas, entregadores, disputas, suspensões), cursor.
- `ux-advanced/search-filter-ux` — busca/filtro cross-área de entregadores/lojas (tela 24).
- `ux-advanced/trust-safety-ux` — suspensão com recurso, transparência do score, decisão de disputa.
- `product/component-library-governance` — reusa jx-data-table/estados/confirmação; novos jx-score-badge/
  jx-score-breakdown/jx-suspension-panel (UI-SPEC).
- `quality/accessibility-pro` — score por cor+texto (daltonismo), SLA countdown aria-live, contraste AA.
- `ux-advanced/design-tokens-system` + `ui-ux-pro-max` — UI-SPEC via tokens (incl. color.score_level.*); zero hex.
- `ux-advanced/dark-mode-theming` (DEC-001) — telas nos 2 temas.
- `ux-advanced/empty-states-polish` — empties de áreas/disputas/suspensões/avaliações.
- `br/ux-copywriting-ptbr` — copy de suspensão/recurso/score sem jargão (UI-SPEC §copy).
- `domain/mysql-schema-design` — migration 0011 (snapshots/ratings/appeals/revenue_share); índices; FK RESTRICT; reversível.
- `domain/fastapi-production-patterns` — módulos platform_admin/scores/ratings/suspensions, jobs arq.

## Skills Dispensadas (com justificativa)
- `domain/safe2pay-escrow-br`/`saas-billing-canonical`/`payment-checkout-ux` — `has_payments: false`; a
  resolução financeira de disputa e o cálculo de revenue share são da Phase 15 (DEC-004). Aqui revenue
  share é só config parametrizada (D-07).
- `mobile/*` — sem superfície mobile.
- `domain/github-actions-ci`/`monorepo-deploy-safety` — flagged por keyword, mas deploy é a Phase 14.

## Threat model (herdado — RESEARCH §Security Baseline)
TH-01 MFA admin (TOTP já obrigatório) · TH-02 acesso cross-área auditado · TH-03 suspensão append-only
auditada · TH-04 require_role em tudo · TH-05 score sem escrita direta · TH-06 injection em filtros
(Pydantic) · TH-07 PII fora de log · TH-08 reversão SLA idempotente. **secure-phase valida.**

## Tech debt deste plano (Regra 11)
- Sem TD vencida nesta phase. **Atenção:** revenue share % (OQ-1) fica `[ASSUMIDO]` parametrizado;
  registrar **TD-13-01** (decisão do % pelo dono, urgency_class `pre_launch_high`) se ainda indefinido.

## LOW confidence → tasks (Regra 12)
- **LOW-1 (RESEARCH §3):** reversão automática por SLA → **Task T-07** com critério: appeal vencido
  sem decisão → subject volta a `active` + alerta; appeal decidido no prazo → sem reversão (clock controlado).

## Tasks (waves)

### Wave 1 — Schema + score + avaliações (backend)
- **T-01** Migration 0011: `courier_score_snapshots`, `courier_ratings`, `suspension_appeals`,
  `area_revenue_share`, seed `score_weights` (area-scoped, FK RESTRICT, índices, reversível + teste @mysql).
- **T-02** Módulo `scores/`: composição parametrizada (pesos do seed), mapeamento de nível, job arq
  diário `snapshot_scores` (idempotente, 1/dia/courier), endpoints (entregador vê o seu; admin vê breakdown).
- **T-03** Módulo `ratings/`: loja avalia entregador pós-FINALIZADA (1-5+comentário), UNIQUE por entrega,
  merchant_scope; alimenta componente do score (peso parametrizado).
- **T-04** Garantir **isolamento ADR-013**: teste provando que score NÃO afeta `dispatch/ranking.py`.

### Wave 2 — Suspensão/recurso + admin plataforma (backend)
- **T-05** Módulo `suspensions/`: abrir suspensão (motivo obrigatório, audit before/after), abrir recurso
  com `sla_due_at`, registrar decisão (upheld/overturned) auditada. Reusa estados existentes.
- **T-06** Endpoints admin de área para disputas (`payment_dispute` Phase 9) + suspensões: triagem +
  decisão administrativa auditada (**sem efeito financeiro** — placeholder explícito p/ Phase 15).
- **T-07** Job arq `enforce_appeal_sla`: appeal vencido sem decisão → reverte subject p/ active + alerta
  (LOW-1, clock controlado, idempotente).
- **T-08** Módulo `platform_admin/`: endpoints cross-área read-mostly (visão geral, busca entregadores/
  lojas + score, lista global disputas/suspensões); **cada acesso cross-área → audit_log** (TH-02);
  `require_platform_admin` (TOTP). Config de revenue share parametrizada (D-07).

### Wave 3 — Frontend (admin plataforma 23-25 + área 09/19/20)
- **T-09** Componentes `jx-score-badge`, `jx-score-breakdown`, `jx-suspension-panel` (+ stories + a11y).
- **T-10** Shell admin de plataforma + telas 23/24/25 (KPIs, busca/filtro, breakdown, disputas globais).
- **T-11** Admin de área: telas 09 (disputas/suspensões), 19/20 (detalhe entregador + score + suspender/recurso).
- **T-12** Serviços Angular + signals; estados empty/loading/error; testes. Zero hex.

## Verificação (ROADMAP)
- SLA de recurso estourado → suspensão revertida + alerta (job testado).
- Snapshot diário de score com componentes/pesos; **nenhum efeito financeiro** ligado a score.
- Admin de plataforma sem TOTP → bloqueado.
- Wireframe-contract de 09, 19, 20, 23, 24, 25.
- `uv run pytest` (not-mysql) + `pytest -m mysql` migration 0011 + `ng test`/build/lint verdes.
- Gate 8: sem segredo/PII em log, suspensão auditada, acesso cross-área auditado, auth definida.

## Parallel-hint
`module-split` — scores ∥ ratings ∥ suspensions ∥ platform_admin são arquivos disjuntos. Wave 1 (schema)
antes; Waves 2 e 3 paralelizáveis.
