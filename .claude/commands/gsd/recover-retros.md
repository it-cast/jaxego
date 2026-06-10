---
name: gsd:recover-retros
description: Reconstrói retrospectivas faltantes a partir de artefatos da phase. Resolve cenário onde autopilot pulou auto-retro ou fluxo manual esqueceu de gerar.
argument-hint: "[--phase N] [--all] [--interactive]"
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

Recupera retrospectivas perdidas. Casos de uso:

1. **Autopilot pulou auto-retro** durante avanço entre phases (bug v0.4.1)
2. **Fluxo manual esqueceu de rodar `/gsd-metrics`** ao fechar phase
3. **Retro foi corrompida ou apagada acidentalmente**
4. **Adoção retroativa do framework** em projeto que já tinha phases executadas

A reconstrução extrai dados objetivos de:
- `.planning/METRICS.md` (entrada da phase)
- `.planning/phases/<N>-<slug>/<N>-PLAN.md` (skills, tasks)
- `.planning/phases/<N>-<slug>/<N>-EXECUTION-LOG.md` (eventos)
- `.planning/phases/<N>-<slug>/<N>-VERIFICATION.md` (gates, gaps)
- `git log` (timestamps, revisions)

Os 5 campos qualitativos são marcados como `[AUTO: preencher depois]` e o humano preenche manualmente. Modo `--interactive` faz as perguntas durante a execução.

</objective>

<execution_context>
@./.claude/get-shit-done/workflows/recover-retros.md
</execution_context>

<context>
Argumentos: $ARGUMENTS

**Flags:**
- `--phase N` — reconstruir uma phase específica (ex: `--phase 3`)
- `--all` — reconstruir TODAS as phases sem retro (default se nenhuma flag)
- `--interactive` — perguntar qualitativos durante a reconstrução
</context>

<process>
Executar workflow `recover-retros.md` end-to-end. Output em pt-BR.
</process>
