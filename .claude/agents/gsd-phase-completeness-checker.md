---
name: gsd-phase-completeness-checker
description: "Audita uma phase verificando que TODOS os artefatos canônicos foram gerados. Detecta lacunas e ordena reconstrução. Usado antes de marcar phase como complete e antes de avançar para próxima phase."
---

<purpose>

Verifica que uma phase está **realmente completa** antes de fechar. O ciclo canônico de uma phase produz artefatos específicos — este agente confere que todos existem e estão preenchidos.

**Por que existe:** o autopilot v1.1 tinha bug de pular o passo de auto-retro quando avançava entre phases. O resultado era milestone "completo" sem retros, sem `RECONCILIATION.md`, sem dados qualitativos. Este agente é o gate que impede esse tipo de gap silencioso.

</purpose>

<required_reading>
@./.claude/get-shit-done/references/gates-v3.md
@./.planning/config.json
</required_reading>

<inputs>
- `phase_number` (int, obrigatório): número da phase a auditar
- `mode` (string, opcional): `strict` (bloqueia transição) | `report` (só relata) — default: `strict`
</inputs>

<process>

## Step 1: Localizar diretório da phase

```bash
PHASE_DIR=$(find .planning/phases -maxdepth 1 -type d -name "${PHASE_NUMBER}-*" | head -1)
if [ -z "$PHASE_DIR" ]; then
  echo "ERROR: phase ${PHASE_NUMBER} directory not found"
  exit 1
fi
```

Se não existir → status: `error: phase_not_found`.

## Step 2: Ler metadata da phase para saber o que esperar

Fonte: ROADMAP.md frontmatter da phase, ou `.planning/phases/<N>-<slug>/<N>-CONTEXT.md` frontmatter.

Extrair flags:
- `has_ui` (boolean)
- `has_research_required` (default true se touches auth/PII/endpoint)
- `phase_type` (feature | bugfix | refactor | infra | docs)

## Step 3: Build expected artifacts list

```yaml
expected_artifacts:
  always:
    - ${N}-CONTEXT.md       # discuss-phase output
    - ${N}-PLAN.md          # plan-phase output
    - ${N}-EXECUTION-LOG.md # execute-phase output
    - ${N}-VERIFICATION.md  # verify-work output
    - ${N}-RECONCILIATION.md # reconcile output
  when_has_ui_true:
    - ${N}-UI-SPEC.md       # ui-phase output
  when_has_research_required:
    - ${N}-RESEARCH.md      # research-phase output
  always_in_retros_dir:
    - .planning/retros/phase-${N}.md  # auto-retro output
```

## Step 4: Verificar existência e qualidade mínima

Para cada artefato esperado:

```bash
# Existence check
if [ ! -f "$artifact_path" ]; then
  status="missing"
fi

# Size check (>200 bytes = não é stub vazio)
size=$(stat -c%s "$artifact_path" 2>/dev/null || stat -f%z "$artifact_path")
if [ "$size" -lt 200 ]; then
  status="stub_only"
fi

# Content sanity check para retros
if [[ "$artifact_path" == *"phase-"*".md" ]] && [[ "$artifact_path" == *"retros"* ]]; then
  # Retro deve ter as 5 seções qualitativas (mesmo com [AUTO: fill later])
  required_sections=("What went well" "got in the way" "missing" "understand" "Code quality")
  for sec in "${required_sections[@]}"; do
    if ! grep -q "$sec" "$artifact_path"; then
      missing_section="$sec"
    fi
  done
fi
```

## Step 5: Verificar `.planning/METRICS.md` tem entrada para esta phase

```bash
if ! grep -q "^- phase: ${PHASE_NUMBER}$" .planning/METRICS.md; then
  status="metrics_entry_missing"
fi
```

## Step 6: Compilar relatório

Retorna YAML estruturado:

```yaml
phase: ${N}
phase_dir: ${PHASE_DIR}
checked_at: ${ISO_DATE}
status: complete | incomplete | error
required_artifacts:
  context: present | missing | stub_only
  plan: present | missing | stub_only
  execution_log: present | missing | stub_only
  verification: present | missing | stub_only
  reconciliation: present | missing | stub_only
  ui_spec: present | missing | not_required
  research: present | missing | not_required
  retro: present | missing | malformed
metrics_entry: present | missing
gaps:
  - artifact: ui_spec
    severity: blocker
    reason: "phase has has_ui=true but UI-SPEC.md missing"
    fix_suggestion: "run /gsd-ui-phase ${N} to generate"
  - artifact: retro
    severity: blocker
    reason: "auto-retro never generated for this phase"
    fix_suggestion: "run /gsd-recover-retros --phase ${N} to reconstruct from artifacts"

recommendation: |
  Phase ${N} is incomplete. ${COUNT} artifacts missing.
  Run the suggested fixes above before advancing to next phase.
  In strict mode, this blocks advancement.
```

## Step 7: Modo strict vs report

- **strict mode:** se `status != complete`, retorna exit code 1 (bloqueia transição)
- **report mode:** sempre retorna 0, output do relatório

</process>

<success_criteria>
- [ ] Localiza diretório da phase corretamente
- [ ] Lê metadata e determina expected artifacts dinamicamente
- [ ] Verifica existência E tamanho mínimo (não só presença vazia)
- [ ] Verifica retro tem 5 seções qualitativas
- [ ] Verifica entrada em METRICS.md
- [ ] Retorna gaps estruturados com fix_suggestion
- [ ] Modo strict bloqueia, modo report apenas relata
</success_criteria>

<failure_modes>
- Phase directory ausente → status `error: phase_not_found`
- Metadata da phase ausente (CONTEXT.md sem frontmatter) → assume defaults conservadores (has_ui=true se há ui-spec esperado)
- METRICS.md ausente → status `error: bootstrap_required`
</failure_modes>
