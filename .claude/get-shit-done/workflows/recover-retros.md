<purpose>

Reconstrói retros faltantes a partir dos artefatos sobreviventes da phase (PLAN.md, EXECUTION-LOG.md, VERIFICATION.md, METRICS.md, git log). Resolve cenário onde autopilot pulou auto-retro ou fluxo manual esqueceu de gerar.

Saída: arquivo `.planning/retros/phase-N.md` populado com:
- Dados objetivos extraídos automaticamente
- Auto-observações inferidas dos artefatos
- 5 campos qualitativos com `[AUTO: preencher depois]` (ou populados se humano fornecer)

</purpose>

<required_reading>
@./.claude/get-shit-done/templates/retrospective.md
@./.claude/get-shit-done/references/gates-v3.md
</required_reading>

<process>

<step name="1-parse-args">

## 1. Parse argumentos

```bash
PHASE_ARG=""
ALL=""
INTERACTIVE=""

# Flags suportadas:
#   --phase N        : reconstruir uma phase específica
#   --all            : reconstruir TODAS as phases que não têm retro
#   --interactive    : fazer perguntas qualitativas para o humano

if echo "$ARGUMENTS" | grep -qE '\-\-phase\s+[0-9]'; then
  PHASE_ARG=$(echo "$ARGUMENTS" | grep -oE '\-\-phase\s+[0-9]+\.?[0-9]*' | awk '{print $2}')
fi
if echo "$ARGUMENTS" | grep -q '\-\-all'; then ALL="true"; fi
if echo "$ARGUMENTS" | grep -q '\-\-interactive'; then INTERACTIVE="true"; fi
```

Se nem `--phase` nem `--all` informados, default = `--all`.

</step>

<step name="2-discover-missing-retros">

## 2. Descobrir retros faltantes

```bash
# Listar todas as phases existentes (diretórios em .planning/phases/)
EXISTING_PHASES=$(ls -d .planning/phases/*/ 2>/dev/null | sed 's|.planning/phases/||;s|/$||' | grep -oE '^[0-9]+\.?[0-9]*' | sort -u)

# Listar retros existentes
EXISTING_RETROS=$(ls .planning/retros/phase-*.md 2>/dev/null | grep -oE '[0-9]+\.?[0-9]*' | sort -u)

# Diff: phases sem retro
MISSING=$(comm -23 <(echo "$EXISTING_PHASES") <(echo "$EXISTING_RETROS"))
```

Se `MISSING` vazio:
> "Todas as phases já têm retros. Nada a fazer."
Exit clean.

Se `--phase N` foi passado mas N já tem retro:
> "Phase N já tem retro em .planning/retros/phase-N.md. Sobrescrever? (y/n)"

</step>

<step name="3-extract-objective-data">

## 3. Extrair dados objetivos para cada phase faltante

Para cada `phase_number` em `MISSING`:

### 3.1 Localizar diretório da phase

```bash
PHASE_DIR=$(find .planning/phases -maxdepth 1 -type d -name "${phase_number}-*" | head -1)
PHASE_NAME=$(basename "$PHASE_DIR" | sed "s/^${phase_number}-//")
```

### 3.2 Extrair de METRICS.md (se entrada existe)

```bash
# Buscar bloco YAML da phase em METRICS.md
metrics_entry=$(awk "/^- phase: ${phase_number}$/,/^---|^- phase:/" .planning/METRICS.md | head -50)
```

Campos extraíveis: `started_at`, `closed_at`, `duration_days`, `gates_bypassed`, `plan_revisions`, `skills_cited`, `skills_dispensed`, `tasks_total`, `tasks_completed`.

### 3.3 Se METRICS.md não tem entrada, fallback via git log

```bash
# Tentar via commits
first_commit=$(git log --all --reverse --format="%aI" --grep="phase.${phase_number}" | head -1)
last_commit=$(git log --all --format="%aI" --grep="phase.${phase_number}" | head -1)
commit_count=$(git log --all --format="%H" --grep="phase.${phase_number}" | wc -l)
plan_revisions=$(git log --all --format="%H" -- "${PHASE_DIR}/${phase_number}-PLAN.md" | wc -l)
```

### 3.4 Extrair tasks de PLAN.md

```bash
# Contar checkboxes
total_tasks=$(grep -cE '^\s*-\s\[[ x]\]' "${PHASE_DIR}/${phase_number}-PLAN.md")
done_tasks=$(grep -cE '^\s*-\s\[x\]' "${PHASE_DIR}/${phase_number}-PLAN.md")
```

### 3.5 Extrair gates de VERIFICATION.md

```bash
# Buscar status de cada gate (se foi documentado)
gates_status=$(awk '/^## Gates/,/^## /' "${PHASE_DIR}/${phase_number}-VERIFICATION.md" 2>/dev/null)
```

### 3.6 Extrair skills citadas de PLAN.md

```bash
skills_cited=$(awk '/^## Skills Consultadas/,/^## /' "${PHASE_DIR}/${phase_number}-PLAN.md" | grep -oE '`[a-z-]+/[a-z-]+`|`[a-z-]+`' | tr -d '`')
skills_dispensed=$(awk '/^## Skills Dispensadas/,/^## /' "${PHASE_DIR}/${phase_number}-PLAN.md" | grep -oE '`[a-z-]+/[a-z-]+`|`[a-z-]+`' | tr -d '`')
```

</step>

<step name="4-infer-auto-observations">

## 4. Inferir auto-observações dos artefatos

Eventos detectáveis automaticamente:

```python
observations = []

# Plan revisado várias vezes = sinal de fricção no planning
if plan_revisions >= 3:
    observations.append(f"PLAN.md foi revisado {plan_revisions} vezes — alta fricção no planejamento")

# Gates bypassados = sinal a investigar
if gates_bypassed > 0:
    observations.append(f"{gates_bypassed} gate(s) foram bypassados — verificar METRICS.md gates_bypassed[]")

# Tech debt aceito = trade-off feito
if tech_debt_added > 0:
    observations.append(f"{tech_debt_added} item(s) de dívida técnica adicionados — ver TECH-DEBT.md")

# Phase rápida demais (suspeita de stub)
if duration_hours and duration_hours < 0.5:
    observations.append("Phase fechou em <30min — verificar se artefatos não são stubs")

# Phase muito longa (estouro de estimativa)
if duration_days and duration_days > 7:
    observations.append("Phase durou >7 dias — recalibrar estimativas para phases similares")

# Code review pegou bugs (verifica se EXECUTION-LOG menciona CR-XX)
cr_bugs = grep -cE 'CR-[0-9]+|WR-[0-9]+' EXECUTION-LOG.md
if cr_bugs > 0:
    observations.append(f"Code review pegou {cr_bugs} bug(s) críticos — destacar em 'O que funcionou bem'")
```

</step>

<step name="5-generate-retro">

## 5. Gerar arquivo de retro

```bash
mkdir -p .planning/retros

cat > .planning/retros/phase-${phase_number}.md << EOF
---
phase: ${phase_number}
phase_name: ${PHASE_NAME}
milestone: ${milestone}
date: ${ISO_DATE}
auto_generated: true
manually_reconstructed: true
reconstructed_at: ${NOW_ISO}
pending_review: true
---

# Retrospectiva — Phase ${phase_number} ${PHASE_NAME}

> ⚠️ Esta retrospectiva foi **reconstruída** a partir dos artefatos sobreviventes da phase, não capturada em tempo real. Dados objetivos foram extraídos de METRICS.md, PLAN.md, EXECUTION-LOG.md, VERIFICATION.md e git log. Os campos qualitativos precisam de preenchimento manual.

## Dados objetivos (extraídos automaticamente)

- **Início:** ${started_at}
- **Fim:** ${closed_at}
- **Duração:** ${duration_days} dias (${duration_hours}h trabalhadas)
- **Plan revisions:** ${plan_revisions}
- **Tasks:** ${done_tasks}/${total_tasks}
- **Gates bypassados:** ${gates_bypassed}
- **Tech debt adicionado:** ${tech_debt_added} item(s)
- **Skills citadas:** ${skills_cited_list}
- **Skills dispensadas:** ${skills_dispensed_list}

## Auto-observações

${observations_list}

## Qualitativo (preencher manualmente — edite este arquivo)

### 1. O que funcionou bem nesta phase?
[AUTO: preencher depois]

### 2. O que atrapalhou?
[AUTO: preencher depois]

### 3. O que faltou (skill, contexto, ferramenta)?
[AUTO: preencher depois]

### 4. Claude entendeu o que você queria? (1-5)
[AUTO: preencher depois]

### 5. Qualidade do código entregue? (1-5)
[AUTO: preencher depois]

## Próximos passos

- [ ] Preencher os 5 campos qualitativos acima
- [ ] Atualizar METRICS.md se há campos que faltam
- [ ] Se há observação relevante para o framework, adicionar a SUGGESTIONS.md
EOF
```

</step>

<step name="6-interactive-mode">

## 6. Modo interativo (opcional)

Se `--interactive` foi passado, fazer 5 perguntas para o humano para cada phase reconstruída:

```
Para Phase ${N} (${PHASE_NAME}):

[1/5] O que funcionou bem nesta phase? (resumo em 1-3 linhas)
> ${user_input}

[2/5] O que atrapalhou? (1-3 linhas)
> ${user_input}

[3/5] O que faltou (skill, contexto, ferramenta)? (1-2 linhas)
> ${user_input}

[4/5] Claude entendeu o que você queria? (1=nada, 5=perfeito)
> ${score_1_5}

[5/5] Qualidade do código entregue? (1=ruim, 5=excelente)
> ${score_1_5}
```

Substituir `[AUTO: preencher depois]` pelas respostas.

</step>

<step name="7-update-metrics">

## 7. Atualizar METRICS.md se necessário

Se a entrada da phase em METRICS.md está incompleta, adicionar/completar:

```yaml
- phase: ${phase_number}
  phase_name: ${PHASE_NAME}
  retro_reconstructed: true
  retro_reconstructed_at: ${NOW_ISO}
  retro_qualitative_filled: ${INTERACTIVE_FLAG}
```

</step>

<step name="8-summary">

## 8. Sumário final

```
✓ Recuperação de retros concluída

Reconstruídas: ${COUNT} phases
  - phase-2.md (qualitativos pendentes)
  - phase-3.md (qualitativos pendentes)
  - phase-4.md (qualitativos pendentes)

Próximos passos:
  1. Abrir cada arquivo em .planning/retros/ e preencher os 5 campos qualitativos
  2. Após preenchidos, rodar: bash bin/export-telemetry.sh
  3. Compartilhar JSON em conversa nova com Claude para análise

Sugestão: usar --interactive da próxima vez para preencher qualitativos durante a recuperação:
  /gsd-recover-retros --all --interactive
```

</step>

</process>

<success_criteria>
- [ ] Detecta phases sem retro automaticamente
- [ ] Extrai dados objetivos de múltiplas fontes (METRICS, git, PLAN, EXECUTION, VERIFICATION)
- [ ] Infere auto-observações relevantes (revisions, gates, tech debt, code review)
- [ ] Gera retro em pt-BR com estrutura completa
- [ ] Marca claramente que é reconstrução, não captura real-time
- [ ] Modo --interactive coleta qualitativos do humano
- [ ] Atualiza METRICS.md com flag retro_reconstructed
- [ ] Idempotente: rodar 2x não duplica nem corrompe
</success_criteria>
