# Framework Metrics — log append-only de uso real

> **Leia antes de usar:**
> Este arquivo registra, fase a fase, dados quantitativos sobre a experiência de uso do GSD Framework.
> Cada entrada representa uma fase fechada. Nunca editar entradas passadas — apenas adicionar novas ao fim.
> 
> Objetivo: gerar base de dados honesta para responder "o framework está ajudando?" e "onde ele atrapalha?".

## Por que isso importa

Sem métricas, qualquer afirmação sobre a qualidade do framework ("subiu a 8.5/10") é opinião. Com métricas,
a discussão vira: "taxa de fix caiu de 12% para 5% entre fase 1 e fase 4 — o framework está puxando peso."

Dados coletados são **anonimizáveis** (nada de PII, nomes reais de projeto ou código privado) —
ver `TELEMETRY-SCHEMA.json` na raiz do framework para o formato exportável.

## Como registrar uma entrada

1. Ao fechar uma fase (`gate 7` passou, feature em produção), rodar: `bin/collect-metrics.sh`
2. O script cria um rascunho com números coletados do diretório `.planning/`
3. Preencher campos qualitativos manualmente (o que atrapalhou? o que ajudou?)
4. Commit do arquivo

## Schema (v1)

```yaml
phase_id: string          # identificador único (ex: "phase-12-orders-api")
started_at: ISO8601
closed_at: ISO8601
duration_days: number

# Planning
plan_revisions: int              # quantas vezes o PLAN.md foi reescrito antes de executar
skills_cited: [string]           # skills listadas em "Skills Consultadas"
skills_dispensed: [string]       # skills listadas em "Skills Dispensadas"
plan_checker_blocks: int         # vezes que plan-checker bloqueou durante planning

# Execução
tasks_total: int
tasks_completed: int
gates_passed: [int]              # ex: [1,2,3,4,5,6,7]
gates_bypassed: [{ gate: int, reason: string }]  # quando --skip-* foi usado
reconcile_runs: int              # vezes que reconcile-state foi invocado
reconcile_divergences_found: int # total de afirmações falsas detectadas

# Qualidade
fix_iterations: int              # quantos PRs de fix logo após o close da fase (proxy de "saiu quebrado")
bugs_reported_7d: int            # bugs abertos em issue tracker nos 7 dias após close
bugs_severity_high: int
rollback: bool                   # rollback em prod aconteceu?

# Experiência (qualitativo, 1 linha cada)
what_worked: string              # o que o framework fez bem nesta fase
what_hurt: string                # o que atrapalhou / fricção desnecessária
what_missing: string             # skill/gate/ferramenta que faltou

# Scoring subjetivo
framework_effort: 1-5            # 1=invisível, 5=muito overhead
framework_value: 1-5             # 1=inútil, 5=salvou muito trabalho
```

---

## Entries

<!-- Novos registros vão abaixo desta linha, um por fase. Nunca editar os anteriores. -->

<!--
EXEMPLO (remover quando começar a registrar de verdade):

### phase-example

```yaml
phase_id: phase-example
started_at: 2026-04-22T10:00:00Z
closed_at: 2026-04-24T18:00:00Z
duration_days: 2.3

plan_revisions: 3
skills_cited: [product/api-design-contracts, br/brazilian-forms, quality/observability-production]
skills_dispensed: [mobile/offline-first, mobile/push-notifications-architecture]
plan_checker_blocks: 2

tasks_total: 7
tasks_completed: 7
gates_passed: [1,2,3,4,5,6,7]
gates_bypassed: []
reconcile_runs: 2
reconcile_divergences_found: 1

fix_iterations: 1
bugs_reported_7d: 0
bugs_severity_high: 0
rollback: false

what_worked: "skill api-design-contracts pegou 3 error codes faltando antes de code review"
what_hurt: "plan-checker bloqueou 2x por falta de skill dispensada explícita — verboso"
what_missing: "skill específica de rate-limiting não existe; tive que improvisar"

framework_effort: 2
framework_value: 4
```
-->

### 04-cadastro-e-ativa-o-de-loja

```yaml
phase_id: 04-cadastro-e-ativa-o-de-loja
started_at: <FILL_AUTO>
closed_at: 2026-06-10T18:01:01Z
duration_days: <FILL>

plan_revisions: 0
skills_cited: []
skills_dispensed: []
plan_checker_blocks: <FILL>

tasks_total: 0
tasks_completed: 0
gates_passed: <FILL>
gates_bypassed: <FILL>
reconcile_runs: 0
0
reconcile_divergences_found: <FILL>

fix_iterations: 4
bugs_reported_7d: <FILL>
bugs_severity_high: <FILL>
rollback: <FILL>

what_worked: "<FILL — 1 linha>"
what_hurt: "<FILL — 1 linha>"
what_missing: "<FILL — 1 linha>"

framework_effort: <FILL 1-5>
framework_value: <FILL 1-5>
```

### 05-cadastro-do-entregador-kyc-2-n-veis-documentos-b2

```yaml
phase_id: 05-cadastro-do-entregador-kyc-2-n-veis-documentos-b2
started_at: <FILL_AUTO>
closed_at: 2026-06-10T20:32:08Z
duration_days: <FILL>

plan_revisions: 0
skills_cited: []
skills_dispensed: []
plan_checker_blocks: <FILL>

tasks_total: 0
tasks_completed: 0
gates_passed: <FILL>
gates_bypassed: <FILL>
reconcile_runs: 1
reconcile_divergences_found: <FILL>

fix_iterations: 4
bugs_reported_7d: <FILL>
bugs_severity_high: <FILL>
rollback: <FILL>

what_worked: "<FILL — 1 linha>"
what_hurt: "<FILL — 1 linha>"
what_missing: "<FILL — 1 linha>"

framework_effort: <FILL 1-5>
framework_value: <FILL 1-5>
```
