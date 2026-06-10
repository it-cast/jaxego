# Workflow: go (v0.9.5)

Roteador de entrada única. Detecta estado do projeto e encadeia os workflows certos com pausas de revisão garantidas. É o caminho de ouro: `projeto/` → sistema rodando.

## 1. Diagnóstico de estado

```bash
HAS_PLANNING=$([ -d .planning ] && [ -f .planning/STATE.md ] && echo 1 || echo 0)
HAS_PROJETO=$(find projeto/ -type f ! -name "README.md" 2>/dev/null | head -1)
STATE_PHASE=$(node .claude/get-shit-done/bin/gsd-tools.cjs state get 2>/dev/null | grep -i "phase" || true)
```

Classificar em exatamente um dos estados:

| Estado | Condição | Rota |
|---|---|---|
| `NOVO_COM_DOCS` | sem `.planning/`, `projeto/` com conteúdo | ingest → bootstrap → autopilot |
| `NOVO_SEM_DOCS` | sem `.planning/`, `projeto/` vazia | orientar projeto/README.md OU discovery interativo |
| `EM_ANDAMENTO` | `.planning/` ok, STATE aponta phase aberta | resume-work |
| `MILESTONE_FECHADO` | `.planning/` ok, milestone atual completo | milestone-summary → próximo milestone |
| `INCONSISTENTE` | STATE diverge de artefatos no disco | health → propor reconcile |

## 2. Anunciar rota (sempre, antes de executar)

Formato fixo, 3 linhas máximo:

```
🧭 Estado detectado: {estado} ({evidência em 1 frase})
Rota: {passo1} → {passo2} → {passo3}
Pausas de revisão: {lista}
```

`--dry-run` → parar aqui. `--status` → parar aqui + mostrar STATE.md resumido.

## 3. Executar rota

### NOVO_COM_DOCS
```
Skill(skill="gsd-ingest")
→ PAUSA 1: mostrar DISCOVERY-REPORT.md, destacar Open Questions críticas
→ AskUserQuestion: "Discovery correto? Ajustar algo antes do bootstrap?"
Skill(skill="gsd-bootstrap")
→ PAUSA 2: mostrar .planning/ROADMAP.md (milestones + phases + flags)
→ AskUserQuestion: "ROADMAP aprovado? Este é o ponto mais barato para corrigir rumo."
[--until=plan? → parar aqui]
Skill(skill="gsd-autopilot", args="M1")
```

### EM_ANDAMENTO
```
Skill(skill="gsd-resume-work")
```
Após resume reportar onde está: oferecer continuar manual ou re-engatar autopilot `--from <phase atual>`.

### MILESTONE_FECHADO / INCONSISTENTE / NOVO_SEM_DOCS
Seguir tabela do §1 — sempre informando o comando granular equivalente, para o humano aprender o framework pelo uso.

## 4. Erros

Qualquer workflow encadeado falhar:
1. Parar a cadeia (nunca pular para o próximo passo)
2. Mostrar erro real + arquivo a inspecionar
3. Indicar comando granular para retomar daquele ponto
4. Registrar em `.planning/SUGGESTIONS.md` se a falha sugerir gap do framework

## Princípio

/gsd:go reduz a superfície de decisão do humano de 93 commands para 1 — sem reduzir o enforcement. Todos os gates, todas as pausas obrigatórias, todo o trilho de artefatos continuam idênticos ao caminho manual.
