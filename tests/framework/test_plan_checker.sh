#!/usr/bin/env bash
# tests/framework/test_plan_checker.sh
# Smoke test do plan-checker: valida detecção de skills obrigatórias e bypasses sem reason.
#
# Implementação de plan-checker ainda não está em binário separado (v0.1 usa lógica inline no workflow).
# Este script simula o que plan-checker deveria fazer via grep, como smoke test.
# Quando plan-checker virar binário real, trocar invocação.

set -u
cd "$( dirname "${BASH_SOURCE[0]}" )"

FAIL=0

# Função simuladora do plan-checker (será trocada por binário real na v0.3)
plan_check() {
  local plan="$1"
  local violations=()
  
  # Gate 3: Skills obrigatórias
  if ! grep -q "^## Skills Consultadas" "$plan" 2>/dev/null; then
    violations+=("missing_section:Skills Consultadas")
  fi
  
  # Detecta task types que exigem skills específicas
  if grep -qiE "endpoint|api/v[0-9]|POST /|@router\." "$plan"; then
    for required in "product/api-design-contracts" "quality/observability-production"; do
      if ! grep -q "$required" "$plan"; then
        violations+=("missing_required_skill:$required")
      fi
    done
  fi
  
  if grep -qiE "CPF|CNPJ|CEP|validação de" "$plan"; then
    if ! grep -q "br/brazilian-forms" "$plan"; then
      violations+=("missing_required_skill:br/brazilian-forms")
    fi
  fi
  
  # Gate bypasses sem reason
  while IFS= read -r flag; do
    if ! grep -qE "\-\-reason(=|[[:space:]]+)" "$plan"; then
      violations+=("gate_bypass_without_reason:$flag")
    fi
  done < <(grep -oE "\-\-skip-gate-[0-9]+" "$plan" 2>/dev/null || true)
  
  if [[ ${#violations[@]} -eq 0 ]]; then
    echo "PASS"
  else
    echo "BLOCK"
    for v in "${violations[@]}"; do
      echo "reason: $v"
    done
  fi
}

# Roda cada fixture e compara com expected.txt
check_fixture() {
  local name="$1"
  local plan="fixtures/$name/PLAN.md"
  local expected="fixtures/$name/expected.txt"
  
  if [[ ! -f "$plan" ]]; then
    echo "FAIL: fixture $name sem PLAN.md"
    FAIL=$((FAIL + 1))
    return
  fi
  
  actual=$(plan_check "$plan")
  expected_content=$(cat "$expected")
  
  # Comparação: todas as linhas de expected devem aparecer em actual (ordem não importa)
  local missing=""
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    if ! echo "$actual" | grep -qF "$line"; then
      missing="${missing}\n  linha esperada faltando: $line"
    fi
  done <<< "$expected_content"
  
  # Primeiro token (PASS ou BLOCK) tem que bater
  expected_verdict=$(head -n1 "$expected" | tr -d ' \n')
  actual_verdict=$(echo "$actual" | head -n1 | tr -d ' \n')
  
  if [[ "$expected_verdict" != "$actual_verdict" ]]; then
    echo "FAIL: $name — verdict esperado '$expected_verdict', obtido '$actual_verdict'"
    echo "  actual output:"
    echo "$actual" | sed 's/^/    /'
    FAIL=$((FAIL + 1))
  elif [[ -n "$missing" ]]; then
    echo "FAIL: $name — razões faltando:$missing"
    echo "  actual output:"
    echo "$actual" | sed 's/^/    /'
    FAIL=$((FAIL + 1))
  else
    echo "OK: $name"
  fi
}

check_fixture "good-plan"
check_fixture "bad-plan-no-skills"
check_fixture "bad-plan-bypass-no-reason"

if [[ $FAIL -eq 0 ]]; then
  echo "plan-checker smoke: $FAIL failures"
  exit 0
else
  echo "plan-checker smoke: $FAIL failures"
  exit 1
fi
