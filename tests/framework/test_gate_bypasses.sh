#!/usr/bin/env bash
# tests/framework/test_gate_bypasses.sh
# Valida 3 cenários de bypass de gate:
# 1. --skip-gate-3 sem --reason → BLOCK
# 2. --skip-gate-3 --reason "justificativa" → ALLOW (com log de warning)
# 3. Sem bypass → NORMAL (passa pelo gate normal)

set -u
cd "$( dirname "${BASH_SOURCE[0]}" )"

FAIL=0

# Simulador — recebe string de "comando" e decide
check_bypass() {
  local input="$1"
  
  if echo "$input" | grep -qE "\-\-skip-gate-[0-9]+"; then
    if echo "$input" | grep -qE "\-\-reason[=[:space:]]+['\"]?\S"; then
      echo "ALLOW_WITH_WARNING"
    else
      echo "BLOCK: bypass sem --reason"
    fi
  else
    echo "NORMAL"
  fi
}

assert_eq() {
  local label="$1" expected="$2" actual="$3"
  if [[ "$expected" == "$actual" ]]; then
    echo "OK: $label"
  else
    echo "FAIL: $label"
    echo "  expected: $expected"
    echo "  actual:   $actual"
    FAIL=$((FAIL + 1))
  fi
}

# Caso 1: bypass sem reason
actual=$(check_bypass "gsd execute-phase --skip-gate-3")
assert_eq "bypass sem reason" "BLOCK: bypass sem --reason" "$actual"

# Caso 2: bypass com reason
actual=$(check_bypass "gsd execute-phase --skip-gate-3 --reason 'hotfix emergencial ticket #1234'")
assert_eq "bypass com reason" "ALLOW_WITH_WARNING" "$actual"

# Caso 2b: bypass com reason via = 
actual=$(check_bypass "gsd execute-phase --skip-gate-6 --reason=hotfix-urgent")
assert_eq "bypass com reason (=)" "ALLOW_WITH_WARNING" "$actual"

# Caso 3: sem bypass
actual=$(check_bypass "gsd execute-phase")
assert_eq "sem bypass" "NORMAL" "$actual"

# Caso 4: múltiplos skips, um sem reason
actual=$(check_bypass "gsd execute-phase --skip-gate-3 --skip-gate-6")
assert_eq "múltiplos bypasses sem reason" "BLOCK: bypass sem --reason" "$actual"

if [[ $FAIL -eq 0 ]]; then
  echo "gate-bypasses smoke: 0 failures"
  exit 0
else
  echo "gate-bypasses smoke: $FAIL failures"
  exit 1
fi
