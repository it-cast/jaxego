---
name: gsd:verify-phase
description: Verifica que phase atende success_criteria do ROADMAP.md. Gera VERIFICATION.md. Output em pt-BR.
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
Verifica phase contra success_criteria definidos em `.planning/ROADMAP.md`.

Diferente de `/gsd-verify-work`:
- `verify-work` é UAT conversacional (humano testa funcionalidade)
- `verify-phase` é check programático (gates 5, 6, 7 + success_criteria do ROADMAP)

Gera `<N>-VERIFICATION.md` na pasta da phase.

Output em pt-BR.
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/verify-phase.md
</execution_context>

<context>
Argumento: $ARGUMENTS

**Posicional obrigatório:**
- `<phase-number>`
</context>

<process>
Executar workflow verify-phase.md end-to-end. Output em pt-BR.
</process>
