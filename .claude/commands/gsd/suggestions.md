---
name: gsd:suggestions
description: |
  Revisa .planning/SUGGESTIONS.md e promove entries para o destino certo:
  backlog, TECH-DEBT.md, ROADMAP (nova phase) ou descarte justificado.

  Origem (v0.9.6): os guias citavam /gsd:suggestions como parte da rotina
  semanal, mas o command nunca existiu — só o hook gsd-suggestion-detector.js
  (que detecta sugestões não-registradas). Este command fecha o ciclo:
  detector grava → suggestions revisa e promove.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

# /gsd:suggestions

Revisão e triagem de sugestões acumuladas durante execução.

## O que faz

1. **Lê** `.planning/SUGGESTIONS.md`. Se não existe ou está vazio, informa e
   lembra que o hook `gsd-suggestion-detector.js` sinaliza quando sugestões
   verbais deixam de ser registradas.
2. **Para cada entry `SUG-NN`**, apresenta e pergunta o destino:
   - **Backlog** → move para `.planning/BACKLOG.md` (mesmo formato de `/gsd:add-backlog`)
   - **Tech debt** → cria linha em `.planning/TECH-DEBT.md` com `urgency_class`
   - **Phase nova** → propõe entrada no ROADMAP (requer confirmação; grava via
     fluxo de `/gsd:add-phase`)
   - **Descartar** → remove, registrando a razão na própria entry antes de
     arquivar em `SUGGESTIONS-ARCHIVE.md` (descarte silencioso é proibido —
     mesma filosofia dos overrides de gate)
3. **Ao final**, remove de `SUGGESTIONS.md` tudo que foi triado e mostra o
   resumo: N promovidas para backlog, N para TD, N para roadmap, N descartadas.

## Quando usar

Rotina semanal, junto com `/gsd:td-review`. Sugestão acumulada sem triagem é
contexto perdido — o detector existe exatamente porque 9 phases consecutivas
fecharam com SUGGESTIONS.md vazio enquanto sugestões verbais se perdiam.

## Invocação

```
/gsd:suggestions
```
