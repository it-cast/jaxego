# Phase 13 — Execution Log (backend, Waves 1-2 / T-01..T-08)

**Executor:** backend (apps/api) · **Escopo:** Waves 1-2 (T-01..T-08). Frontend (Wave 3) NÃO executado.
**Data:** 2026-06-11 · **Branch:** master · **Migration:** 0011

## Tarefas concluídas

| Task | Descrição | Commit |
|------|-----------|--------|
| T-01 | Migration 0011 + modelos (scores/ratings/suspensions/revenue_share) | `1ec44f9` |
| T-02 | Score explicável: composição parametrizada, snapshot diário idempotente, endpoints | `96be4e3` |
| T-04 | Isolamento ADR-013 (score × dispatch/ranking) — teste | `96be4e3` |
| T-03 | Avaliações loja→entregador pós-FINALIZADA (UNIQUE/escopo) | `5ab3d42` |
| T-05/06/07/08 | Suspensão/recurso + reversão SLA + disputas + admin plataforma | `ddafcc6` |

## Decisões de implementação (Claude's discretion — registradas)

- **Composição do score:** soma ponderada `raw(0..1) × peso(seed) × 100`; pesos seed
  somam 1.0 (acceptance .25 / punctuality .25 / proof_ok .20 / low_cancellation .15 /
  ratings .15). Bandas de nível: diamante≥90, ouro≥75, prata≥55, bronze≥35, probation≥0.
  Tudo parametrizável (DRV-009) — bandas são banda de apresentação, sem efeito financeiro.
- **Sinais do score:** derivados de dados existentes (ratings avg + razão de conclusão de
  entregas). `acceptance_rate`/`punctuality` usam proxy de conclusão no M1 (ver TD-13-02).
  Prior neutro 0.5 para entregador sem histórico (não pune novato).
- **SLA de recurso:** janela default 72h (`[ASSUMIDO]`, parametrizável). Reversão por job
  marca `reverted_at` (idempotente). Teste com clock controlado via `sla=timedelta(hours=-1)`
  para forçar vencido sem mexer no relógio do sistema.
- **Revenue share:** seed `[ASSUMIDO]` 10% (TD-13-01). Tabela versionada por `effective_from`
  (estilo ADR-103). Endpoint de escrita auditado; NÃO move dinheiro (DEC-004 → Phase 15).
- **Disputas (T-06):** decisão administrativa marca `payment_dispute.status=resolved` +
  audit; placeholder explícito de comentário no service para a consequência financeira da
  Phase 15 (bloqueio 90d/restituição NÃO implementados).

## Segurança (Gate 4 — TH-01..TH-08)

- TH-01 TOTP: reusa `require_platform_admin` (bloqueio sem TOTP testado via HTTP).
- TH-02 cross-área: cada leitura do platform_admin grava audit_log `cross_area_bypass=True` (testado).
- TH-03 suspensão append-only: transições via audit_log (trigger MySQL já bloqueia UPDATE/DELETE).
- TH-04 require_role/require_platform_admin em todos os endpoints (admin_area não acessa platform — testado).
- TH-05 score read-only: NENHUM endpoint de escrita de nota; snapshot derivado pelo job.
- TH-06 filtros bound: Pydantic/Query + LIKE parametrizado (teste com payload de injection).
- TH-07 PII fora de log: agregados de score usam só counts/stars; audits só ids/states.
- TH-08 reversão idempotente: aware-UTC, `reverted_at` guard (testado idempotência).

## Desvios das regras (deviation rules)

- **[Rule 3]** A migration 0011 precisou registrar os novos mappers em `tests/conftest.py`
  para o `Base.metadata.create_all` do SQLite enxergar as tabelas (bloqueava import dos testes).
- Nenhum desvio arquitetural (Rule 4). Nenhum bug pré-existente corrigido fora de escopo.

## Tech debt registrada

- **TD-13-01** (pre_launch_high) — revenue share % `[ASSUMIDO]` 10%, decisão do dono antes da Phase 15.
- **TD-13-02** (post_launch_quarter) — proxies de sinal de score (acceptance/punctuality) para v1.1.

## Itens NÃO executados (fora de escopo deste executor)

- Wave 3 (frontend T-09..T-12) — admin plataforma 23-25 + área 09/19/20.
- Consequência financeira de disputa/score (Phase 15 / DEC-004).
- Teste `@pytest.mark.mysql` da migration 0011 escrito mas NÃO rodado aqui (roda contra MySQL live).

---

# Phase 13 — Execution Log (frontend, Wave 3 / T-09..T-12)

**Executor:** frontend (apps/web) · **Escopo:** Wave 3 (T-09..T-12). **Data:** 2026-06-11
**Branch:** master · **Angular 19 + Ionic 8, standalone/signals/OnPush, lazy por rota.**

## Tarefas concluídas

| Task | Descrição | Commit |
|------|-----------|--------|
| T-09 | Componentes jx-score-badge, jx-score-breakdown, jx-suspension-panel (+ stories + specs + a11y) | `29d559b` |
| T-12 | Serviços Angular de governança (PlatformAdminService + GovernancaService) | `1967a0e` |
| T-10 | Shell admin de plataforma + telas 23/24/25 | `dc2054e` |
| T-11 | Admin de área — telas 09 + 19/20 | `6940455` |
| T-12 | Specs de serviços + estados (signals/empty/loading/error) das telas | `9954d81` |

## Componentes novos (T-09)

- `jx-score-badge` — nível + cor do token `--score-*` + label textual (cor+texto, daltonismo);
  variantes md/lg; valor em mono pt-BR. Exportado no barrel (`ScoreBadgeLevel` para evitar
  colisão com o `ScoreLevel` do score-chip existente).
- `jx-score-breakdown` — tabela explicável (componente | valor | peso | contribuição) +
  footer de total + nota "informativo no piloto" (ADR-013). `<th scope>` + caption sr-only.
- `jx-suspension-panel` — motivo + janela de recurso + SLA countdown (`aria-live="polite"`,
  tick 1/min) + ações manter/reverter; estados aberta/risco/vencida/revertida/mantida.

## Telas (T-10/T-11)

- **Plataforma (novo shell lazy `/plataforma`, só renderiza; backend exige TOTP+platform_admin):**
  23 (KPIs mono + lista de áreas com badge info `% parametrizado`), 24 (busca/filtro cross-área
  + jx-score-badge → drawer jx-score-breakdown; aviso info "score não afeta despacho nem cobrança"),
  25 (disputas globais + jx-suspension-panel).
- **Área (rotas no shell `/admin` existente):** 09 (disputas com decisão administrativa
  procedente/improcedente + aviso "resolução financeira no módulo financeiro" — sem efeito
  financeiro; recursos via jx-suspension-panel), 19/20 (detalhe entregador + score + breakdown +
  suspender com motivo obrigatório → recurso + SLA).

## Serviços (T-12)

- `PlatformAdminService` (`/v1/platform/*` + `/v1/admin/scores/*`) e `GovernancaService`
  (`/v1/admin/suspensions|disputes`, `/v1/admin/scores`). Contratos espelham os schemas do backend.

## Decisões de implementação (Claude's discretion)

- **score-badge ≠ score-chip:** o piloto já tinha `jx-score-chip` (inline, células). O UI-SPEC pede
  `jx-score-badge` — criado como badge maior para detalhe (telas 19/20/24) reusando os mesmos
  `--score-*`. Ambos coexistem; nenhum hex.
- **Filtro de score na tela 24** abre um drawer com breakdown (reuso do `--surface-sunken` como
  backdrop, padrão dos modais da api-keys; sem token `--scrim`, que não existe).
- **Histórico de avaliações (telas 19/20):** o backend NÃO expõe endpoint de listagem de ratings;
  a contribuição das avaliações aparece no `jx-score-breakdown` (componente `ratings`). Lista
  detalhada de avaliações registrada como TD-13-03.
- **`as` em `@else if`:** Angular 19 só permite `as` no `@if` primário — breakdown movido para um
  `@if` aninhado dentro do `@else`.

## Desvios das regras (deviation rules)

- **[Rule 3]** SLA countdown precisava de `aria-live` e tick — implementado com `setInterval`
  limpo via `DestroyRef` (sem vazamento). Sem desvio arquitetural (Rule 4).
- Nenhum bug pré-existente corrigido fora de escopo.

## Tech debt registrada

- **TD-13-03** (post_launch_quarter) — endpoint + UI de histórico detalhado de avaliações
  (loja→entregador) nas telas 19/20; hoje a contribuição aparece só agregada no score breakdown.

## Gates / verificação

- Gate 7: `npm run test` (177 SUCCESS), `npm run build` e `npm run lint` verdes.
- Zero hex confirmado nas pastas novas (`admin-plataforma/`, `admin/governanca/`, os 3 componentes,
  o shell): `grep -rn "#[0-9A-Fa-f]{3,6}"` → 0.
- A11y: score badge cor+texto; modais role=dialog/aria-modal/Esc; SLA countdown aria-live;
  tabelas `<th scope>` + teclado.
