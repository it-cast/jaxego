#!/usr/bin/env bash
# tests/framework/run-all.sh
# Roda todos os smoke tests do framework GSD

set -u
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

RED=$(printf '\033[0;31m')
GREEN=$(printf '\033[0;32m')
YELLOW=$(printf '\033[1;33m')
RESET=$(printf '\033[0m')

echo "=== GSD Framework smoke tests ==="
echo ""

PASS=0
FAIL=0
SUITES=(
  "test_structure.sh"
  "test_plan_checker.sh"
  "test_reconcile.sh"
  "test_gate_bypasses.sh"
  "test_sprint_checker.sh"
  "test_state_integrity.sh"
  "test_v095_additions.sh"
  "test_quality_bar_gate.sh"
  "test_docs_consistency.sh"
  "test_partition.sh"
  "test_wireframe_fidelity.sh"
)

for suite in "${SUITES[@]}"; do
  if [[ ! -f "$suite" ]]; then
    echo "${YELLOW}⚠${RESET}  $suite não encontrado (pulando)"
    continue
  fi
  
  echo "→ $suite"
  if bash "$suite" > /tmp/gsd-test-$$.log 2>&1; then
    echo "  ${GREEN}✓${RESET}  passed"
    PASS=$((PASS + 1))
  else
    echo "  ${RED}✗${RESET}  FAILED"
    echo "  ---output---"
    sed 's/^/    /' /tmp/gsd-test-$$.log
    echo "  ---end---"
    FAIL=$((FAIL + 1))
  fi
  rm -f /tmp/gsd-test-$$.log
  echo ""
done

TOTAL=$((PASS + FAIL))
echo "==============================="
if [[ $FAIL -eq 0 ]]; then
  echo "${GREEN}$PASS/$TOTAL suites passed${RESET}"
  exit 0
else
  echo "${RED}$FAIL/$TOTAL suites FAILED${RESET}  ($PASS passed)"
  exit 1
fi
