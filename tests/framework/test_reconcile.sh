#!/usr/bin/env bash
# tests/framework/test_reconcile.sh
# Valida que reconcile-state detecta divergência entre PLAN.md (tasks [x]) e código real.
#
# v0.1 usa grep inline no workflow. Este script simula para smoke test.

set -u
cd "$( dirname "${BASH_SOURCE[0]}" )"

FAIL=0

# Simulador de reconcile — compara afirmações de PLAN.md com código da fixture
reconcile() {
  local dir="$1"
  local plan="$dir/PLAN.md"
  local issues=()
  local presents=()
  
  # Extrai nomes de tabelas/endpoints/funções mencionados em [x] tasks
  # Simplificado: apenas casos pré-definidos que a fixture testa
  
  # Pasta onde procurar código real (exclui PLAN.md e expected.txt)
  local code_dir="$dir"
  
  # T1: migration "create_audit_log_table"
  if grep -qE "^\-\s+\[x\].*migration.*audit_log" "$plan" 2>/dev/null; then
    if ! find "$code_dir" -path '*/migrations/*' -name "*audit_log*" 2>/dev/null | grep -q .; then
      issues+=("missing: migration:create_audit_log_table")
    fi
  fi
  
  # T2: função log_audit_event — grep excluindo PLAN.md e expected.txt
  if grep -qE "^\-\s+\[x\].*log_audit_event" "$plan" 2>/dev/null; then
    if grep -rq --exclude='PLAN.md' --exclude='expected.txt' "def log_audit_event" "$code_dir" 2>/dev/null; then
      presents+=("present: function:log_audit_event")
    else
      issues+=("missing: function:log_audit_event")
    fi
  fi
  
  # T3: middleware de audit — exclui metadata do fixture
  if grep -qE "^\-\s+\[x\].*[Mm]iddleware.*audit" "$plan" 2>/dev/null; then
    if ! grep -rqE --exclude='PLAN.md' --exclude='expected.txt' \
         "(audit_middleware|AuditMiddleware|class.*Audit.*Middleware)" "$code_dir" 2>/dev/null; then
      issues+=("missing: middleware:audit_middleware")
    fi
  fi
  
  # T4: endpoint admin/audit-log — exclui metadata do fixture
  if grep -qE "^\-\s+\[x\].*[Ee]ndpoint.*audit" "$plan" 2>/dev/null; then
    if ! grep -rqE --exclude='PLAN.md' --exclude='expected.txt' \
         "(/admin/audit-log|admin_audit_log|audit.*router)" "$code_dir" 2>/dev/null; then
      issues+=("missing: endpoint:/api/v1/admin/audit-log")
    fi
  fi
  
  if [[ ${#issues[@]} -eq 0 ]]; then
    echo "CLEAN"
    for p in "${presents[@]}"; do echo "$p"; done
  else
    echo "DIVERGENCE"
    for i in "${issues[@]}"; do echo "$i"; done
    for p in "${presents[@]}"; do echo "$p"; done
  fi
}

# Fixture 1: divergência esperada
check_divergence_fixture() {
  local actual
  actual=$(reconcile "fixtures/reconcile-divergence")
  
  local expected
  expected=$(cat "fixtures/reconcile-divergence/expected.txt")
  
  local expected_verdict
  expected_verdict=$(head -n1 <<< "$expected" | tr -d ' \n')
  local actual_verdict
  actual_verdict=$(echo "$actual" | head -n1 | tr -d ' \n')
  
  if [[ "$expected_verdict" != "$actual_verdict" ]]; then
    echo "FAIL: reconcile-divergence verdict esperado '$expected_verdict', obtido '$actual_verdict'"
    echo "$actual" | sed 's/^/    /'
    FAIL=$((FAIL + 1))
    return
  fi
  
  # Confere que os "missing" esperados aparecem
  local missing=""
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    [[ "$line" == "$expected_verdict" ]] && continue
    if ! echo "$actual" | grep -qF "$line"; then
      missing="${missing}\n  faltando: $line"
    fi
  done <<< "$expected"
  
  if [[ -n "$missing" ]]; then
    echo "FAIL: reconcile-divergence detectou menos issues que o esperado:$missing"
    echo "  actual:"
    echo "$actual" | sed 's/^/    /'
    FAIL=$((FAIL + 1))
  else
    echo "OK: reconcile-divergence"
  fi
}

# Fixture 2: good-plan não deve gerar divergência (nenhuma task [x] ainda)
check_clean_fixture() {
  local actual
  actual=$(reconcile "fixtures/good-plan")
  local verdict
  verdict=$(echo "$actual" | head -n1 | tr -d ' \n')
  
  if [[ "$verdict" != "CLEAN" ]]; then
    echo "FAIL: good-plan deveria ser CLEAN (nenhum [x]), obtido '$verdict'"
    echo "$actual" | sed 's/^/    /'
    FAIL=$((FAIL + 1))
  else
    echo "OK: good-plan (CLEAN)"
  fi
}

check_divergence_fixture
check_clean_fixture

if [[ $FAIL -eq 0 ]]; then
  echo "reconcile smoke: 0 failures"
  exit 0
else
  echo "reconcile smoke: $FAIL failures"
  exit 1
fi
