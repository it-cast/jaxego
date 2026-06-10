<purpose>
Planner de fase v3 — aplica gates bloqueantes antes, durante e depois do planejamento.
Diferença vs. v2: gates de UI-SPEC (Gate 2), Security Baseline (Gate 4) e Skills Coverage (Gate 3) agora BLOQUEIAM, não apenas alertam.
</purpose>

<required_reading>
@$CLAUDE_PROJECT_DIR/CLAUDE.md
@$CLAUDE_PROJECT_DIR/.claude/get-shit-done/references/gates-v3.md
@$CLAUDE_PROJECT_DIR/.claude/get-shit-done/references/skills-enforcement.md
@$CLAUDE_PROJECT_DIR/.planning/ROADMAP.md
@$CLAUDE_PROJECT_DIR/.planning/config.json
</required_reading>

<trigger>
/gsd-plan-phase <N>                           # planeja phase N
/gsd-plan-phase <N> --skip-ui --reason "..."  # override Gate 2 (raro)
/gsd-plan-phase <N> --skip-security --reason "..."  # override Gate 4 (raro)
/gsd-plan-phase <N> --revision                # re-roda após plan-checker BLOCK
</trigger>

<process>

## 1. Gate 1 — Bootstrap

```bash
if [ ! -f .planning/PROJECT.md ]; then
  echo "❌ Bootstrap não executado. Rode /gsd-bootstrap primeiro."
  exit 1
fi
```

## 2. Parsear argumentos e detectar metadata

O plan-phase pode receber **duas formas** de input, dependendo se o projeto usa sprints (default a partir de v0.2.1) ou fases diretas (legado):

- **Sprint-aware (default):** argumento é um `sprint_id` (ex: `sprint-03-create-listing`). Workflow lê o `SPRINT.md` correspondente em `.planning/sprints/` e herda metadata do front-matter YAML.
- **Phase-legacy:** argumento é um `phase_id` (ex: `phase-05-payment`). Workflow lê metadata direto do `ROADMAP.md`.

```bash
INPUT=$1
SKIP_UI=false
SKIP_SECURITY=false
OVERRIDE_REASON=""

# Detecção automática do modo
if [[ -f ".planning/sprints/${INPUT}.md" ]]; then
  MODE="sprint"
  SPRINT_FILE=".planning/sprints/${INPUT}.md"
  
  # Ler front-matter YAML (entre --- e ---)
  PHASE_UI=$(read_front_matter "$SPRINT_FILE" "has_ui")
  PHASE_HAS_FORMS=$(read_front_matter "$SPRINT_FILE" "has_forms")
  PHASE_HAS_ERROR_STATES=$(read_front_matter "$SPRINT_FILE" "has_error_states")
  PHASE_HAS_MOTION=$(read_front_matter "$SPRINT_FILE" "has_non_trivial_motion")
  PHASE_TOUCHES_SHARED=$(read_front_matter "$SPRINT_FILE" "touches_shared_components")
  PHASE_LOCALE=$(read_front_matter "$SPRINT_FILE" "locale")
  PHASE_MOBILE=false  # sprints podem setar se aplicável
  
  # Sprint já tem ## Visual Contract embutido — UI-SPEC não é gerado separado
  # Gate 2 vira "Visual Contract present + tokens válidos"
  
elif grep -q "^## PHASE $INPUT" .planning/ROADMAP.md 2>/dev/null; then
  MODE="phase"
  PHASE=$INPUT
  PHASE_UI=$(extract_flag "$PHASE" "ui")
  PHASE_MOBILE=$(extract_flag "$PHASE" "mobile")
  PHASE_INTEGRATION=$(extract_flag "$PHASE" "integration_check")
  
else
  echo "ERRO: '$INPUT' não é sprint (não existe em .planning/sprints/) nem fase (não aparece em ROADMAP.md)"
  echo ""
  echo "Se você usa sprints (recomendado), rode primeiro:"
  echo "  /gsd-sprint-plan <milestone-id>"
  echo "Para gerar os SPRINT.md antes de chamar /gsd-plan-phase."
  exit 1
fi

# Detectar características de risco de segurança (comum aos dois modos)
PHASE_HAS_RISK=$(detect_security_risk "$INPUT" "$MODE")
```

## 3. Gate 2 — UI-SPEC / Visual Contract bloqueante

### Se MODE = sprint

Já há `## Visual Contract` no SPRINT.md (validado por `/gsd-sprint-plan` ao gerar). Este passo re-valida que:

1. Seção presente (se `has_ui: true`)
2. Todo token citado existe em `docs/identidade-visual/tokens.json`
3. Skills UX obrigatórias foram listadas em `## Skills Consultadas`, conforme matriz `sprint_ui_matrix` em `references/skills-enforcement.md`

Lógica idêntica à do `tests/framework/test_sprint_checker.sh` — sprint-checker é autoridade.

```bash
if [[ "$MODE" == "sprint" && "$PHASE_UI" == "true" && "$SKIP_UI" != "true" ]]; then
  if ! has_section "$SPRINT_FILE" "## Visual Contract"; then
    echo "BLOCK: sprint com has_ui:true sem seção ## Visual Contract"
    exit 1
  fi
  
  # Valida tokens contra tokens.json
  violations=$(validate_visual_tokens "$SPRINT_FILE" "docs/identidade-visual/tokens.json")
  if [[ -n "$violations" ]]; then
    echo "BLOCK: tokens citados no Visual Contract não existem em tokens.json:"
    echo "$violations"
    exit 1
  fi
fi
```

### Se MODE = phase (legado)

Mantém lógica original (UI-SPEC.md em arquivo separado).

```bash
if [ "$PHASE_UI" = "true" ] && [ "$SKIP_UI" != "true" ]; then
  UI_SPEC_PATH=".planning/phases/$(padded $PHASE)-*/UI-SPEC.md"
  if [ ! -f $UI_SPEC_PATH ]; then
    cat <<EOM
❌ Phase $PHASE declara ui=true no ROADMAP, mas UI-SPEC.md não existe.

Gate 2 (UI-SPEC bloqueante) ativo.

Rode primeiro:
  /gsd-ui-phase $PHASE $([ "$PHASE_MOBILE" = "true" ] && echo "--mobile")

UI-SPEC define tokens, tipografia, copy, estados, micro-interações ANTES do código.
Pular isso causa redesigns retroativos.

Para override (raro): /gsd-plan-phase $PHASE --skip-ui --reason "<texto>"
EOM
    exit 1
  fi
fi
```

Se override `--skip-ui` foi usado, registrar em `.planning/DECISIONS.md`:

```markdown
## {date} — Override Gate 2 (UI-SPEC) em Phase {N}

- **Razão:** {OVERRIDE_REASON}
- **Risco assumido:** design ad-hoc nesta fase
- **Follow-up:** rodar /gsd-ui-phase {N} em fase seguinte se houver retrabalho
```

## 4. Gate 4 — Security Baseline

Se a fase tem características de risco:

```bash
if [ "$PHASE_HAS_RISK" = "true" ] && [ "$SKIP_SECURITY" != "true" ]; then
  RESEARCH_PATH=".planning/phases/$(padded $PHASE)-*/RESEARCH.md"
  if [ ! -f $RESEARCH_PATH ]; then
    echo "❌ Phase $PHASE tem risco de segurança mas RESEARCH.md não existe."
    echo "Rode: /gsd-research-phase $PHASE --security-focus"
    exit 1
  fi

  # Verificar seção Security Baseline
  if ! grep -q "^## Security Baseline" "$RESEARCH_PATH"; then
    echo "❌ RESEARCH.md não tem seção ## Security Baseline."
    echo "Phase $PHASE toca: {lista dos riscos detectados}"
    echo "Rode: /gsd-research-phase $PHASE --security-focus"
    exit 1
  fi
fi
```

## 5. Invocar `gsd-phase-researcher` (se ainda não rodou)

Se não há `RESEARCH.md` E a fase tem risco OU complexidade declarada, invocar researcher antes do planner. Caso contrário, pular direto para planner.

## 6. Invocar `gsd-planner` com contexto enriquecido

Contexto passado ao planner:
- `.planning/phases/<N>-<slug>/CONTEXT.md`
- `.planning/phases/<N>-<slug>/UI-SPEC.md` (se existe)
- `.planning/phases/<N>-<slug>/RESEARCH.md` (se existe)
- `.planning/ROADMAP.md` (bloco desta fase)
- `specs/stack.yaml`, `specs/rules.yaml`, `specs/database.yaml`
- `SKILLS_INDEX.md` (para saber quais skills estão disponíveis)
- Última `STATE.md` (contexto de onde paramos)

Instrução ao planner:
> Gere PLAN.md usando o template `.claude/get-shit-done/templates/PLAN.md`.
> **Obrigatório** preencher as seções:
> - Skills Consultadas (com regras específicas, não placeholder)
> - Skills Dispensadas (com justificativa)
> - Threat model (se fase tem risco — extrair de Security Baseline do RESEARCH.md)
> - Performance budget (se fase tem UI ou endpoint)
> - Observability checklist (se fase tem endpoint ou job)
> - Error UX checklist (se fase tem UI)
> - Integration contracts (se fase tem integration_check)
>
> Cada task deve ter campo `skills_applied` com as skills e regras específicas aplicadas.

## 7. Gate 3 — Skills Coverage (via `gsd-plan-checker`)

Invocar `gsd-plan-checker`:

```python
# Pseudocódigo do checker
skills = load_all_skills_with_triggers()
plan = parse_plan_md(".planning/phases/{N}-{slug}/PLAN.md")

cited = extract_cited_skills(plan, section="Skills Consultadas")
dispensed = extract_dispensed_skills(plan, section="Skills Dispensadas")

total_missing_across_tasks = 0
task_blocks = []

for task in plan.tasks:
    required = determine_required_skills(task, skills)
    missing = required - cited - dispensed
    if missing:
        total_missing_across_tasks += len(missing)
        task_blocks.append((task, missing))

# Gate 3 thresholds
if total_missing_across_tasks >= 2:
    status = "BLOCK"
elif total_missing_across_tasks == 1:
    status = "FLAG"
else:
    status = "PASS"
```

### Plan-checker também verifica seções obrigatórias presentes

```python
required_sections = {
    "Skills Consultadas": True,  # sempre
    "Skills Dispensadas (com justificativa)": True,  # sempre
    "Threat model": phase_has_risk,
    "Performance budget": phase_has_ui or phase_has_endpoint,
    "Observability checklist": phase_has_endpoint,
    "Error UX checklist": phase_has_ui,
    "Integration contracts": phase_has_integration_check,
}
missing_sections = [s for s, req in required_sections.items() if req and not plan.has_section(s)]
if missing_sections:
    status = "BLOCK"
```

### Se status = BLOCK

Devolver relatório ao planner (loop de revisão — máximo 3 iterações):

```
PLAN-CHECKER: BLOCK

Gate 3 (Skills Coverage) falhou.

Tasks com skills faltando:
- T-03 (criar endpoint /auth/login)
  Exigem: owasp-security, api-design-contracts, observability-production
  Citadas: api-design-contracts
  Missing: owasp-security, observability-production

Seções obrigatórias faltando: Threat model, Observability checklist

Total de skills ausentes: 4.

Revise o PLAN.md:
1. Adicione as skills em ## Skills Consultadas com regras específicas
2. OU dispense explicitamente em ## Skills Dispensadas com justificativa técnica
3. Complete as seções obrigatórias

Re-invocar: /gsd-plan-phase {N} --revision
```

Planner incorpora feedback e re-emite PLAN.md. Re-roda plan-checker. Max 3 iterações. Se ainda BLOCK: escalar ao humano.

### Se status = FLAG

Prosseguir mas registrar warning em DECISIONS.md.

### Se status = PASS

Continuar para etapa 8.

## 8. Persistir artefatos

```bash
# PLAN.md está em .planning/phases/{N}-{slug}/PLAN.md
# Plan-checker report anexado ao final do PLAN.md em seção "Plan-checker report"

# Atualizar STATE.md
# Atualizar REQUIREMENTS.md se plano referenciar REQs novos
# Atualizar EXECUTION-LOG.md da fase com entry "plan-phase"
```

## 9. Mensagem final

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► PLAN-PHASE — Phase {N}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Gates bloqueantes verificados:
  ✓ Gate 1 (Bootstrap)
  ✓ Gate 2 (UI-SPEC) — UI-SPEC.md encontrado [{N} telas cobertas]
  ✓ Gate 4 (Security Baseline) — Security Baseline no RESEARCH.md [{N} ameaças mapeadas]

PLAN.md gerado em .planning/phases/{N}-{slug}/PLAN.md
  • Tasks: {N} em {W} waves
  • Skills consultadas: {list}
  • Skills dispensadas: {list}
  • Threat model: {N} ameaças + mitigações
  • Performance budget: {resumo}
  • Observability checklist: {N/A ou presente}
  • Error UX checklist: {N/A ou presente}
  • Integration contracts: {N/A ou {N} contratos}

Plan-checker: {PASS após N iteração(ões)}

Próximo passo:
  /gsd-execute-phase {N}
```

</process>

<failure_modes>
- **Plan-checker entra em loop infinito** — fix: limite 3 iterações, depois escalar para humano
- **Researcher não produziu Security Baseline apesar de detecção de risco** — fix: auto-invoke `gsd-phase-researcher --security-focus` antes de abortar
- **Override `--skip-*` usado sem razão documentada** — fix: recusar override sem `--reason`
- **UI-SPEC existe mas está vazio/incompleto** — fix: ui-checker já validou, mas plan-phase também faz sanity check (mínimo de N seções presentes)
</failure_modes>
