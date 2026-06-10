---
name: gsd:bootstrap
description: |
  Inicializa o planning do projeto. v0.9.1+ detecta automaticamente:
  - Se projeto/ tem conteúdo → redireciona para /gsd:ingest (caminho automático)
  - Se docs/project-brief.md + specs/ existem → fluxo clássico
  - Se nada existe → orienta operador a escolher
argument-hint: "[--force] [--input=DIR]"
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

# /gsd:bootstrap

Inicializa o planning de um projeto. Comando deve ser rodado **uma vez por projeto**, na raiz.

## Os 3 caminhos

### Caminho A — Automático via `projeto/` (recomendado v0.9.1+)

Se você tem material em qualquer formato (PDFs, wireframes HTML, imagens, MD, YAML):

```
# 1. Coloque tudo em projeto/{regras-negocio, wireframes, identidade-visual, stacks, ...}
# 2. Execute:
/gsd:bootstrap
# → Detecta projeto/, redireciona automaticamente para /gsd:ingest
# → Ingestor lê tudo, gera .planning/ completo + DISCOVERY-REPORT.md
```

### Caminho B — Manual via specs canônicos (clássico v0.8.x)

Se você prefere preencher specs manualmente:

```
# 1. Crie docs/project-brief.md (12 seções padronizadas)
# 2. Crie specs/project.yaml
# 3. Crie specs/stack.yaml
# 4. Execute:
/gsd:bootstrap
# → Detecta specs, gera .planning/ a partir deles
```

### Caminho C — Não inicializado

Se nem `projeto/` tem conteúdo nem `docs/specs` existem, bootstrap orienta:

```
/gsd:bootstrap
# → Mostra opções A e B, sugere começar pela A
```

## Argumentos

- `--force` — sobrescreve `.planning/` existente (use com cuidado)
- `--input=DIR` — usa pasta alternativa em vez de `projeto/`

## Próximo passo depois do bootstrap

```
/gsd:autopilot {milestone-id}    # executa milestone inteiro
```

ou

```
/gsd:discuss-phase               # se quiser executar phase-por-phase
```

## Invocação

Você é o orquestrador. Para esta tarefa:

1. **Leia** `@./.claude/get-shit-done/workflows/bootstrap.md`
2. **Execute** o `<routing_decision>` lá definido — detecta `projeto/` vs specs vs nada
3. **Se caminho A:** acione `/gsd:ingest` com os argumentos passados
4. **Se caminho B:** siga o `<process>` clássico do workflow
5. **Se caminho C:** mostre o guia ao operador e termine
