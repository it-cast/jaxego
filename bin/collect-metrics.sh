#!/usr/bin/env bash
# bin/collect-metrics.sh
#
# Ao fechar uma fase, roda este script para gerar rascunho de entrada em .planning/METRICS.md.
# Coleta automaticamente o que dá pra extrair do sistema de arquivos + git.
# Campos qualitativos ficam como <FILL> para você preencher manualmente.
#
# Uso:
#   bin/collect-metrics.sh phase-12-orders-api
#
# Output:
#   - Append de rascunho em .planning/METRICS.md sob cabeçalho "### phase-12-orders-api"
#   - Campos quantitativos preenchidos automaticamente
#   - Campos qualitativos com <FILL> — editar antes de commit

set -u
cd "$( git rev-parse --show-toplevel 2>/dev/null || pwd )"

PHASE_ID="${1:-}"
if [[ -z "$PHASE_ID" ]]; then
  echo "Uso: $0 <phase-id>"
  echo "Ex:  $0 phase-12-orders-api"
  exit 1
fi

METRICS_FILE=".planning/METRICS.md"
if [[ ! -f "$METRICS_FILE" ]]; then
  echo "ERRO: $METRICS_FILE não encontrado — você está na raiz do framework?"
  exit 1
fi

PLAN="${PLAN_PATH:-.planning/PLAN.md}"
STATE="${STATE_PATH:-.planning/STATE.md}"

# ---------- Coleta automática ----------

now_iso() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

# Quando a fase começou: primeira aparição de arquivos em .planning/ (aproximado via git)
started_at="<FILL_AUTO>"
if [[ -d .git ]]; then
  first_commit=$(git log --reverse --format=%aI -- "$PLAN" 2>/dev/null | head -n1)
  [[ -n "$first_commit" ]] && started_at="$first_commit"
fi
closed_at=$(now_iso)

# Duração (best-effort)
duration_days="<FILL>"
if [[ "$started_at" != "<FILL_AUTO>" ]]; then
  if command -v python3 >/dev/null; then
    duration_days=$(python3 -c "
from datetime import datetime
s = datetime.fromisoformat('$started_at'.replace('Z','+00:00'))
e = datetime.fromisoformat('$closed_at'.replace('Z','+00:00'))
print(f'{(e-s).total_seconds()/86400:.1f}')
" 2>/dev/null || echo "<FILL>")
  fi
fi

# Plan revisions — número de commits que tocaram o PLAN.md
plan_revisions=0
if [[ -d .git && -f "$PLAN" ]]; then
  plan_revisions=$(git log --oneline -- "$PLAN" 2>/dev/null | wc -l | tr -d ' ')
fi

# Skills citadas em PLAN.md
skills_cited="[]"
skills_dispensed="[]"
if [[ -f "$PLAN" ]]; then
  # Extrai bullets entre "## Skills Consultadas" e a próxima "##"
  cited=$(awk '
    /^## Skills Consultadas/ { inside=1; next }
    /^## / && inside { inside=0 }
    inside && /^\s*-\s+`/ {
      match($0, /`[^`]+`/);
      if (RSTART) { print substr($0, RSTART+1, RLENGTH-2) }
    }
  ' "$PLAN" 2>/dev/null | paste -sd, - | sed 's/,/, /g')
  [[ -n "$cited" ]] && skills_cited="[$cited]"
  
  dispensed=$(awk '
    /^## Skills Dispensadas/ { inside=1; next }
    /^## / && inside { inside=0 }
    inside && /^\s*-\s+`/ {
      match($0, /`[^`]+`/);
      if (RSTART) { print substr($0, RSTART+1, RLENGTH-2) }
    }
  ' "$PLAN" 2>/dev/null | paste -sd, - | sed 's/,/, /g')
  [[ -n "$dispensed" ]] && skills_dispensed="[$dispensed]"
fi

# Tasks totais e completadas (contagem de - [ ] e - [x])
tasks_total=0
tasks_completed=0
if [[ -f "$PLAN" ]]; then
  tasks_total=$(grep -cE '^\s*-\s+\[.\]' "$PLAN" 2>/dev/null || echo 0)
  tasks_completed=$(grep -cE '^\s*-\s+\[x\]' "$PLAN" 2>/dev/null || echo 0)
fi

# Gates passed/bypassed — extrai de STATE.md se existir
gates_passed="<FILL>"
gates_bypassed="<FILL>"
if [[ -f "$STATE" ]]; then
  passed=$(grep -oE 'gate[_-]?[0-9]+[:= ]*(passed|ok|✓)' "$STATE" 2>/dev/null | grep -oE '[0-9]+' | sort -u | paste -sd, -)
  [[ -n "$passed" ]] && gates_passed="[$passed]"
  bypassed=$(grep -E '\-\-skip-gate' "$STATE" 2>/dev/null | head -5)
  [[ -n "$bypassed" ]] && gates_bypassed="[\"$(echo "$bypassed" | tr '\n' ';' | sed 's/;$//')\"]"
fi

# Reconcile runs — contar no STATE.md ou em log
reconcile_runs="<FILL>"
if [[ -f "$STATE" ]]; then
  count=$(grep -cE 'reconcile[_-]state' "$STATE" 2>/dev/null || echo 0)
  reconcile_runs="$count"
fi

# Fix iterations — commits com "fix" após o closed_at estimado (últimos 7 dias)
fix_iterations=0
bugs_reported_7d="<FILL>"
if [[ -d .git ]]; then
  fix_iterations=$(git log --since="7 days ago" --oneline --grep="^fix" 2>/dev/null | wc -l | tr -d ' ')
fi

# ---------- Montagem do rascunho ----------

DRAFT=$(cat <<EOF

### $PHASE_ID

\`\`\`yaml
phase_id: $PHASE_ID
started_at: $started_at
closed_at: $closed_at
duration_days: $duration_days

plan_revisions: $plan_revisions
skills_cited: $skills_cited
skills_dispensed: $skills_dispensed
plan_checker_blocks: <FILL>

tasks_total: $tasks_total
tasks_completed: $tasks_completed
gates_passed: $gates_passed
gates_bypassed: $gates_bypassed
reconcile_runs: $reconcile_runs
reconcile_divergences_found: <FILL>

fix_iterations: $fix_iterations
bugs_reported_7d: $bugs_reported_7d
bugs_severity_high: <FILL>
rollback: <FILL>

what_worked: "<FILL — 1 linha>"
what_hurt: "<FILL — 1 linha>"
what_missing: "<FILL — 1 linha>"

framework_effort: <FILL 1-5>
framework_value: <FILL 1-5>
\`\`\`
EOF
)

echo "$DRAFT" >> "$METRICS_FILE"

echo ""
echo "✓ Rascunho adicionado em $METRICS_FILE"
echo ""
echo "Próximos passos:"
echo "  1. Abra $METRICS_FILE"
echo "  2. Localize a entrada '### $PHASE_ID'"
echo "  3. Substitua os <FILL> com os dados reais (3 linhas qualitativas + scores 1-5)"
echo "  4. Commit: git add $METRICS_FILE && git commit -m \"metrics: close $PHASE_ID\""
echo ""
echo "Dica: para exportar anonimizado (para compartilhar com Anthropic/autor do framework):"
echo "  bin/export-telemetry.sh $PHASE_ID"
