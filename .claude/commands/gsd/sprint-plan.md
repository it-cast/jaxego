---
name: gsd:sprint-plan
description: Quebra um milestone em sprints/phases testáveis seguindo a estratégia de slicing. Output em pt-BR.
argument-hint: "<milestone-id>"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Task
  - TodoWrite
  - AskUserQuestion
---

<objective>
Quebrar milestone definido em `.planning/ROADMAP.md` em sequência de phases testáveis.

Lê:
- `.planning/ROADMAP.md` (definição do milestone)
- `.planning/config.json > slicing_strategy` (vertical_value | admin_first)
- `specs/project.yaml > project.apps[]` (estrutura monorepo)

Gera:
- `.planning/SPRINTS.md` ou phases em `.planning/phases/<N>-<slug>/` com estrutura inicial

Output em pt-BR.
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/gsd-sprint-plan.md
</execution_context>

<context>
Argumento: $ARGUMENTS

**Posicional obrigatório:**
- `<milestone-id>` — ex: `v1.0`, `M1-foundation`
</context>

<process>
Executar workflow gsd-sprint-plan.md end-to-end. Output em pt-BR.
</process>
