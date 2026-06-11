# Phase 13: UI-SPEC — Governança (telas 23/24/25 plataforma + 09/19/20 área)

**Status:** Visual contract — bloqueante (Gate 2) · **Date:** 2026-06-11 (autopilot)
**Design system:** `docs/identidade-visual/tokens.json`. **Zero hex.** Dark mode (DEC-001).
**Superfícies:** Web admin de plataforma (telas 23-25, novo shell) + web admin de área (09/19/20).

## Escopo de UI
Telas 23 (visão geral plataforma), 24 (entregadores/lojas cross-área + score), 25 (disputas/
suspensões globais); e no admin de área: 09 (disputas/suspensões da área), 19/20 (detalhe entregador
com score + ação de suspensão/recurso). Mobile: nenhum.

## Componentes (governados — reuso obrigatório)
### Reuso
- `jx-data-table` (Phase 6) — todas as listas (áreas, entregadores, disputas, suspensões)
- estados empty/error/loading (Phase 3); confirmação sensível before→after (Phase 6) — suspender/reverter
- `jx-badge`/state badge (Phase 7) — status de disputa/suspensão
### Novo
- `jx-score-badge` — nível do score com cor do token `color.score_level.{probation|bronze|prata|ouro|diamante}`
- `jx-score-breakdown` — tabela explicável (componente | valor | peso | contribuição) — transparência (ADR-013)
- `jx-suspension-panel` — motivo + janela de recurso + SLA countdown + ação decisão (auditada)

## Tokens (todos existem em tokens.json — Gate 2)
### Score (níveis)
- `color.score_level.probation`, `.bronze`, `.prata`, `.ouro`, `.diamante` (badge + breakdown)
### Status / semântica
- disputa aberta / SLA em risco: `color.semantic.warning` / `warning_bg`
- suspensão ativa / disputa procedente: `color.semantic.error` / `error_bg`
- reativado / improcedente: `color.semantic.success` / `success_bg`
- informativo (revenue share config, score sem efeito): `color.semantic.info` / `info_bg`
### Cores base / tipografia / forma
- Texto: `color.neutral.900/600/400`; superfícies `color.neutral.50/100/200`; marca `color.brand.500/600`
- Título: `font.family.display` `font.size.2xl` `font.weight.bold`; números/score: `font.family.mono`
- Corpo: `font.family.body` `font.size.base`; ênfase `font.weight.semibold`
- Cartões `radius.lg` `shadow.sm`; pílulas `radius.full`; foco `shadow.focus`

## Layout & estados
### Tela 23 — Visão geral da plataforma
Cards de KPI (áreas ativas, entregadores, lojas, entregas) em mono; lista de áreas (jx-data-table)
com volume e revenue share configurado (badge info "% parametrizado"). Empty: "Nenhuma área ainda".

### Tela 24 — Entregadores/lojas cross-área + score
jx-data-table com busca/filtro (search-filter-ux): nome, área, `jx-score-badge`, nível, último uso.
Linha → painel `jx-score-breakdown` (explicável). Aviso info: "Score não afeta despacho nem
cobrança no piloto" (ADR-013). Acesso cross-área registra auditoria (sem UI extra; backend).

### Tela 25 / Tela 09 — Disputas & suspensões
jx-data-table de disputas (`payment_dispute`) + suspensões: tipo | sujeito | área | status | SLA |
ações. `jx-suspension-panel` para registrar decisão (procedente/improcedente — **sem efeito
financeiro nesta phase**, aviso explícito "resolução financeira no módulo financeiro"). Confirmação
sensível na suspensão/reversão. Empty: "Nenhuma disputa/suspensão".

### Tela 19/20 — Detalhe do entregador (área)
Score + breakdown; histórico de avaliações; botão suspender (motivo obrigatório → audit) e ver
recurso (SLA countdown; reversão automática indicada quando o SLA vence).

## Acessibilidade (accessibility-pro)
- Contraste AA nos 2 temas (score_level e semânticos calibrados). Tabelas com header scope + teclado.
- `jx-suspension-panel`: ações com label acessível; SLA countdown com `aria-live` discreto.
- Score badge: cor + **texto** do nível (nunca só cor — daltonismo).

## Copy (br/ux-copywriting-ptbr)
- pt-BR canônico. "Suspender pausa o acesso do entregador. É necessário informar o motivo."
- Recurso: "Se não houver decisão até {prazo}, a suspensão é revertida automaticamente."
- Score: "Score é informativo no piloto — não altera ofertas nem valores."

## Performance
- Rotas lazy. Listas globais paginadas (cursor). LCP = KPIs/lista, não breakdown.

---
*Gate 2: todos os tokens citados existem em tokens.json (incl. color.score_level.*). Zero hex.*
