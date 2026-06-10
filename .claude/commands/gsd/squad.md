---
name: gsd:squad
description: |
  Dispara um squad de agents em paralelo. 3 squads disponíveis:
  research (pre-phase), review (post-execute), audit (pre-release).
---

# /gsd:squad

Dispara squad de agents paralelos para acelerar trabalho onde paralelismo faz sentido.

## Squads disponíveis

### squad-research (pre-phase)

Antes de `/gsd:discuss-phase`, dispara em paralelo:
- `gsd-domain-researcher` — regras de negócio relevantes
- `gsd-ui-researcher` — padrões UX para essa phase
- `gsd-ai-researcher` — componente LLM se aplicável
- `gsd-security-auditor` — threat model antecipado

Output: `docs/squad-outputs/research-{phase}-{date}.md` com síntese e Open Questions.

**Uso:**
```
/gsd:squad research --phase=07
/gsd:squad research --phase=07 --skip=ai     # pular dimensões irrelevantes
```

### squad-review (post-execute)

Depois de `/gsd:execute-phase` concluir, dispara em paralelo:
- `gsd-code-reviewer` — estrutura, padrões, dead code
- `gsd-security-auditor` — vulnerabilidades
- `gsd-integration-checker` — contratos FE↔BE
- `gsd-ui-auditor` — acessibilidade, UX

Output: `docs/squad-outputs/review-{phase}-{date}.md` com priorização.

**Uso:**
```
/gsd:squad review --phase=07
```

### squad-audit (pre-release)

Antes de `/gsd:complete-milestone`, dispara em paralelo:
- `gsd-performance-auditor` (web vitals, query N+1)
- `gsd-accessibility-auditor` (WCAG)
- `gsd-i18n-auditor` (locales, RTL)
- `gsd-observability-auditor` (Sentry, metrics, logs)

Output: `docs/squad-outputs/audit-{milestone}-{date}.md` com gaps para fechar antes do release.

**Uso:**
```
/gsd:squad audit --milestone=v1.1
```

## Quando usar

**Use squad quando:**
- ✅ Phase complexa com múltiplas perspectivas
- ✅ Pre-release ou pre-milestone (audit profundo justifica custo)
- ✅ Sente que serial está perdendo tempo

**Não use squad quando:**
- ❌ Phase trivial (custo de tokens > valor)
- ❌ Você só precisa de uma perspectiva específica (chame o agent direto)
- ❌ Contexto muito tight (squad fragmenta)

## Latência e custo

- Latência total: ~2-3min (paralelo) vs ~8-12min (serial dos 4 agents)
- Tokens: ~4x de uma execução single-agent
- Qualidade: comparável ou superior em síntese final (perspectivas diversas pegam coisas que single-pass perde)

## Invocação

Você é o orquestrador principal. Para esta tarefa:

1. **Parse** os argumentos (`research|review|audit`, `--phase`, `--milestone`, `--skip`)
2. **Acione** o agent `gsd-squad-orchestrator` via Task tool, passando squad e contexto
3. **Aguarde** retorno (o squad-orchestrator faz a paralelização interna)
4. **Mostre** o relatório final ao usuário, destacando Open Questions e prioridades
5. **Sugira** próximo passo (ex: depois de squad-research → `/gsd:discuss-phase`)
