---
name: gsd:metrics
description: Fecha phase capturando métricas em METRICS.md e gerando retrospectiva auto em .planning/retros/. Output em pt-BR.
argument-hint: "<phase-number>"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Task
  - TodoWrite
---

<objective>
Capturar métricas ao fechar phase. Output em pt-BR.

Gera/atualiza:
- `.planning/METRICS.md` (entrada YAML para a phase)
- `.planning/retros/phase-N.md` (retrospectiva com dados objetivos + qualitativos placeholder)
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/gsd-metrics.md
</execution_context>

<context>
Argumento: $ARGUMENTS

**Posicional:**
- `<phase-number>` — número da phase a fechar (ex: 3, 72.1)

**Opcionais:**
- `--interactive` — perguntar qualitativos durante a captura
</context>

<process>
Executar workflow gsd-metrics.md end-to-end. Output em pt-BR. Garantir que retro É gerada (esta é a falha que precisamos não repetir).
</process>
