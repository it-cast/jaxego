---
name: gsd:reconcile-state
description: Reconcilia o que foi prometido no PLAN.md vs o que o código realmente entregou. Gera RECONCILIATION.md. Output em pt-BR.
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
Compara afirmações do `<N>-PLAN.md` com o código realmente entregue na phase. Detecta:

- Promessas no plan não implementadas (gap)
- Código extra não previsto no plan (scope creep)
- Testes que cobrem cada afirmação (true claim)
- Afirmações que código não sustenta (nyquist failure)

Gera `<N>-RECONCILIATION.md` na pasta da phase.

Output em pt-BR.
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/reconcile-state.md
</execution_context>

<context>
Argumento: $ARGUMENTS

**Posicional obrigatório:**
- `<phase-number>` — ex: 3, 72.1
</context>

<process>
Executar workflow reconcile-state.md end-to-end. Output em pt-BR.
</process>
