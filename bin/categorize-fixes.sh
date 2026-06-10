#!/usr/bin/env bash
# bin/categorize-fixes.sh
#
# Categoriza commits "fix" por origem para diferenciar:
# - fix(review): fix pós code-review (esperado — framework funcionou)
# - fix(integration): fix pós integration-checker (esperado)
# - fix(escape): fix por bug que escapou do executor (problemático)
# - fix(*): outros (lint, build, etc.)
#
# Resolve o problema do diagnóstico v0.7.x onde "fix rate 31.9%" é uma
# métrica ambígua que mistura comportamento esperado (fix de review)
# com sinal real (bug escapou) sem distinção.
#
# Uso:
#   bin/categorize-fixes.sh                 # análise da última semana
#   bin/categorize-fixes.sh --since="2 weeks ago"
#   bin/categorize-fixes.sh --milestone v1.1
#   bin/categorize-fixes.sh --phase 09
#
# Saída: contagem por categoria + ratio "escape_rate" (saúde do framework)

set -u

SINCE="1 week ago"
MILESTONE=""
PHASE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --milestone) MILESTONE="$2"; shift 2 ;;
    --phase) PHASE="$2"; shift 2 ;;
    -h|--help)
      echo "Uso: $0 [--since DATE] [--milestone vX.Y] [--phase NN]"
      exit 0 ;;
    *) echo "Argumento desconhecido: $1"; exit 1 ;;
  esac
done

cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || {
  echo "ERRO: não está em repo git"
  exit 1
}

# Construir filtro
GIT_RANGE=()
if [[ -n "$MILESTONE" ]]; then
  # Encontrar tags do milestone
  PREV_TAG=$(git tag -l | grep -E "^v" | sort -V | grep -B1 "^${MILESTONE}" | head -1 | grep -v "${MILESTONE}" || true)
  if [[ -n "$PREV_TAG" ]]; then
    GIT_RANGE=("${PREV_TAG}..HEAD")
  fi
elif [[ -n "$PHASE" ]]; then
  # Filtrar commits que tocam phases/NN-*
  PHASE_FILTER="-- phases/${PHASE}-*"
fi

# Função: contar commits matching pattern
count_matching() {
  local pattern="$1"
  local since_args=()
  if [[ ${#GIT_RANGE[@]} -eq 0 ]]; then
    since_args=(--since="$SINCE")
  fi

  local count
  count=$(git log "${since_args[@]}" "${GIT_RANGE[@]}" --oneline --grep="$pattern" 2>/dev/null | wc -l | tr -d ' ')
  echo "$count"
}

REVIEW=$(count_matching '^fix(review)')
INTEGRATION=$(count_matching '^fix(integration)')
ESCAPE=$(count_matching '^fix(escape)')
LINT=$(count_matching '^fix(lint)')
BUILD=$(count_matching '^fix(build)')
TYPECHECK=$(count_matching '^fix(typecheck)')
TEST=$(count_matching '^fix(test)')

# Outros: tudo que tem "fix:" mas não casa com categorias acima
ALL_FIX=$(count_matching '^fix')

# Calcular "outros" — fix que não tem escopo conhecido
KNOWN=$((REVIEW + INTEGRATION + ESCAPE + LINT + BUILD + TYPECHECK + TEST))
OTHER=$((ALL_FIX - KNOWN))
[[ $OTHER -lt 0 ]] && OTHER=0

# All commits no range para calcular taxa
since_args=(--since="$SINCE")
[[ ${#GIT_RANGE[@]} -gt 0 ]] && since_args=()
TOTAL_COMMITS=$(git log "${since_args[@]}" "${GIT_RANGE[@]}" --oneline 2>/dev/null | wc -l | tr -d ' ')
FEAT=$(count_matching '^feat')

# Saídas
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Fix Categorization Report (GSD v0.8)"
echo "═══════════════════════════════════════════════════════════"
echo ""
if [[ ${#GIT_RANGE[@]} -gt 0 ]]; then
  echo "  Range: ${GIT_RANGE[*]}"
elif [[ -n "$PHASE" ]]; then
  echo "  Phase: $PHASE"
else
  echo "  Since: $SINCE"
fi
echo ""
echo "  Total commits: $TOTAL_COMMITS"
echo "  Features: $FEAT"
echo "  Fixes (todos): $ALL_FIX"
echo ""
echo "  Breakdown de fixes:"
printf "  %-18s %3d (%s)\n" "fix(review)"      "$REVIEW"      "esperado: fix pós code-review"
printf "  %-18s %3d (%s)\n" "fix(integration)" "$INTEGRATION" "esperado: fix pós integration-check"
printf "  %-18s %3d (%s)\n" "fix(escape)"      "$ESCAPE"      "🚨 bug escapou do executor"
printf "  %-18s %3d (%s)\n" "fix(lint)"        "$LINT"        "neutro: lint"
printf "  %-18s %3d (%s)\n" "fix(build)"       "$BUILD"       "neutro: build"
printf "  %-18s %3d (%s)\n" "fix(typecheck)"   "$TYPECHECK"   "neutro: typecheck"
printf "  %-18s %3d (%s)\n" "fix(test)"        "$TEST"        "neutro: testes"
printf "  %-18s %3d (%s)\n" "fix outros"       "$OTHER"       "sem escopo categorizado"
echo ""
echo "  ─── Saúde do framework ───"
echo ""

if [[ $TOTAL_COMMITS -eq 0 ]]; then
  echo "  Sem commits no range."
  exit 0
fi

# Escape rate = % de commits que são fix(escape)
ESCAPE_RATE=$(awk "BEGIN {printf \"%.1f\", $ESCAPE * 100 / $TOTAL_COMMITS}")
EXPECTED_RATE=$(awk "BEGIN {printf \"%.1f\", ($REVIEW + $INTEGRATION) * 100 / $TOTAL_COMMITS}")

printf "  Escape rate (bug escapou): %s%%  " "$ESCAPE_RATE"
if (( $(awk "BEGIN {print ($ESCAPE_RATE < 5) ? 1 : 0}") )); then
  echo "✓ excelente (< 5%)"
elif (( $(awk "BEGIN {print ($ESCAPE_RATE < 10) ? 1 : 0}") )); then
  echo "✓ saudável (< 10%)"
elif (( $(awk "BEGIN {print ($ESCAPE_RATE < 25) ? 1 : 0}") )); then
  echo "⚠ aceitável mas alto (10-25%)"
else
  echo "🚨 alto demais (> 25%) — investigar plan-checker e gates"
fi

printf "  Expected rate (review+int): %s%%  " "$EXPECTED_RATE"
echo "framework está pegando bugs antes de bater ramo principal"

echo ""
echo "  ─── Dica ───"
echo ""
echo "  Adote convenção em mensagens de commit:"
echo "    fix(review): ...      → fix por code-review (esperado)"
echo "    fix(integration): ... → fix por integration-checker (esperado)"
echo "    fix(escape): ...      → bug que escapou (sinal real)"
echo ""
echo "  Sem essa convenção, fix rate vira métrica ambígua que"
echo "  mistura comportamento esperado com sinal."
echo "═══════════════════════════════════════════════════════════"
