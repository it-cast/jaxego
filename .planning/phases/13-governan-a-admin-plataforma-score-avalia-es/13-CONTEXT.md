# Phase 13: Governança — admin plataforma, score, avaliações, suspensão/recurso - Context

**Gathered:** 2026-06-11 (modo --auto, autopilot)
**Status:** Ready for planning

<domain>
## Phase Boundary

Camada de governança do piloto: (a) **admin de plataforma** (telas 23-25) com acesso cross-área
auditado e TOTP obrigatório (já existe); (b) **score explicável** do entregador (REQ-020) — snapshot
diário com componentes/pesos, **sem consequência financeira no M1** (ADR-013); (c) **avaliações**
pós-entrega (REQ-033); (d) **suspensão/recurso com reversão automática** (REQ-045 — SLA estourado →
reverte + alerta); (e) UI de **disputas/suspensões no admin de área** (REQ-044 completo) sobre o
primitivo `payment_dispute` da Phase 9. **Fora de escopo (DEC-004):** resolução FINANCEIRA da disputa
(2 procedentes/30d → bloqueio 90d, restituição) → Phase 15. **Revenue share %** entra como superfície
parametrizada de config (DRV-009), sem movimentar dinheiro (isso é Phase 10/15).
</domain>

<decisions>
## Implementation Decisions

### Score explicável (REQ-020, ADR-013)
- **D-01:** Score é **snapshot diário** (job arq) em `courier_score_snapshots` com os **componentes e
  pesos** explícitos (ex.: taxa de aceite, pontualidade, comprovação ok, cancelamentos) → nota +
  **nível** mapeado aos 5 tokens existentes: `probation/bronze/prata/ouro/diamante`.
- **D-02:** **Zero efeito financeiro/operacional** no M1 (ADR-013): score é exibido (entregador vê o
  seu; admin vê com breakdown), nunca altera ranking de despacho nem fatura. Componentes/pesos
  parametrizados (seed editável, DRV-009), nunca hardcoded.

### Avaliações (REQ-033)
- **D-03:** Avaliação da **loja → entregador** após FINALIZADA (1-5 + comentário opcional), tabela
  `courier_ratings` (area-scoped, 1 por entrega, append). Alimenta um componente do score (peso
  parametrizado). Sem avaliação reversa pública no M1.

### Suspensão / recurso (REQ-045)
- **D-04:** Suspensão de entregador/loja usa as máquinas de estado existentes (courier:
  active↔suspended↔banned; merchant análogo). Suspensão **sempre auditada** (before/after, motivo).
- **D-05:** **Recurso com SLA**: ao suspender, abre janela de recurso. Job arq verifica SLA; **SLA
  estourado sem decisão → reversão automática** para active + **alerta** (REQ-045 verificação). Toda
  transição append-only/auditada.

### Admin de plataforma (REQ-046, telas 23-25)
- **D-06:** Reusa `require_platform_admin` (TOTP já obrigatório — ADR-005). Acesso cross-área é
  **auditado** (cada leitura sensível cross-área gera audit_log — A01/RN-012). Telas: 23 (visão geral
  da plataforma/áreas), 24 (entregadores/lojas cross-área + score), 25 (disputas/suspensões globais).
- **D-07:** **Revenue share** (REQ-047 `[DECIDIR %]`): superfície de **configuração parametrizada** por
  área (valor `[ASSUMIDO]`, seed editável) exibida no admin de plataforma. **Não** calcula/move
  dinheiro nesta phase (fica para o financeiro — Phase 10/15). Decisão do % é do dono (OQ-1) e entra
  como dado, não como código.

### Disputas/suspensões no admin de área (REQ-044 completo)
- **D-08:** Tela do admin de área lista as **disputas** (`payment_dispute` da Phase 9) e **suspensões**
  da sua área, com ação de registrar decisão administrativa (procedente/improcedente) — mas a
  **consequência financeira** (bloqueio 90d, restituição) é **deferida à Phase 15** (DEC-004). Aqui é
  o shell de triagem + registro auditado da decisão.

### Claude's Discretion
- Fórmula exata de composição do score, layout fino das telas 23-25, paginação das listas globais.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Decisões e regras
- `.planning/DECISIONS.md` — ADR-013 (score sem consequência M1, exibido com componentes) · ADR-005
  (TOTP admin plataforma) · DEC-004 (resolução financeira de disputa → Phase 15) · DRV-009 (valores
  parametrizados) · DRV-002 (append-only/audit)
- `.planning/ROADMAP.md` — Phase 13 (REQs 046/020/033/045/047/044; verificações; wireframes 09/19/20/23/24/25)
- RN-008/014/016 · `projeto/regras-negocio/visao-geral.md:29`
- **OQ-1** (revenue share %) — tratar como dado parametrizado, decisão do dono

### Padrões de código a reusar (já no repo)
- `apps/api/app/auth/dependencies.py` — `require_platform_admin` (TOTP), `require_role`, `area_scope`
- `apps/api/app/couriers/state_machine.py` + `app/merchants/state_machine.py` — suspensão (active↔suspended↔banned)
- `apps/api/app/audit/` — audit_log append-only (before/after) — reusar em suspensão e acesso cross-área
- `payment_dispute` (Phase 9) — `app/proofs/` / `app/deliveries/` — primitivo de disputa
- `app/workers/` — padrão de job arq aware-UTC idempotente (snapshot de score + SLA de recurso)
- `app/dispatch/ranking.py` — onde score NÃO deve interferir no M1 (verificar isolamento — ADR-013)

### UI / tokens
- `docs/identidade-visual/tokens.json` — `color.score_level.*` (probation/bronze/prata/ouro/diamante)
- skills: `ux-advanced/saas-dashboard-patterns`, `data-tables-ux`, `search-filter-ux`, `trust-safety-ux`
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `require_platform_admin` já força TOTP — admin de plataforma sem TOTP → bloqueado (verificação ROADMAP) já garantido.
- Máquinas de estado de courier/merchant já têm `suspended` — a suspensão/recurso adiciona a janela de SLA + job de reversão, não novos estados.
- `audit_log` append-only (trigger MySQL) — suspensão e acesso cross-área herdam auditoria.
- `payment_dispute` da Phase 9 — a UI de disputas consome o que já existe; só registra decisão administrativa (sem financeiro).

### Established Patterns
- Módulo = model/schemas/repo/service/router. Jobs arq aware-UTC idempotentes. Snapshot diário = padrão novo simples.
- Score parametrizado (seed) — espelha como planos/taxas são seeds (DRV-009).

### Integration Points
- Novos routers em `app/api/v1/router.py` (bloco Phase 13).
- Telas 23-25 no shell admin de plataforma (novo) + telas 09/19/20 no admin de área (existente).
</code_context>

<specifics>
## Specific Ideas
- Score deve ser **explicável**: o admin vê o breakdown (componente → valor → peso → contribuição),
  não só a nota final. Transparência é requisito (ADR-013), não enfeite.
- Suspensão nunca silenciosa: sempre motivo + auditoria + janela de recurso clara.
</specifics>

<deferred>
## Deferred Ideas
- Consequência financeira de disputa/score (bloqueio 90d, restituição, score→fatura) — Phase 15 / v1.1.
- Score com consequência operacional (ranking) — v1.1 (ADR-013, 90 dias de dados).
- Avaliação pública/reversa entregador→loja — backlog.
</deferred>

---

*Phase: 13-governan-a-admin-plataforma-score-avalia-es*
*Context gathered: 2026-06-11*
