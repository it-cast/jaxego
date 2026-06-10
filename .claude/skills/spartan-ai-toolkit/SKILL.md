---
name: spartan-ai-toolkit
description: >
  Quality gates, TDD enforcement, e atomic commits para desenvolvimento
  com IA. Use para garantir disciplina de engenharia: testes antes de
  mergear, commits atomicos, code review obrigatorio, e gates de qualidade.
---

# Spartan AI Toolkit

## Gate 1 — Pre-Code
- [ ] Requisito claro e documentado
- [ ] Schema/model definido
- [ ] Endpoint planejado (method, path, request, response)
- [ ] Casos de teste identificados

## Gate 2 — Post-Code
- [ ] Type hints em todas as funcoes (Python)
- [ ] Sem any no TypeScript
- [ ] Docstrings em portugues
- [ ] HTTPException com codigos corretos
- [ ] Pydantic para input E output

## Gate 3 — Pre-Commit
- [ ] Lint passa (ruff / eslint)
- [ ] Format aplicado (ruff format / prettier)
- [ ] Testes passam
- [ ] Nenhum secret no codigo
- [ ] Conventional Commits

## Gate 4 — Pre-Merge
- [ ] Code review feito
- [ ] Security audit feito
- [ ] Cobertura >= 80%
- [ ] Nenhum TODO critico
- [ ] CLAUDE.md atualizado se schema mudou

## TDD: Red-Green-Refactor
1. Escreva o TESTE primeiro (Red)
2. Codigo minimo para passar (Green)
3. Refatore mantendo testes verdes (Refactor)

## Atomic Commits
Cada commit: UMA coisa, mensagem descritiva, testes passam, nao quebra build.
