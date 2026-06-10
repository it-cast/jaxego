#!/usr/bin/env bash
# tests/framework/test_sprint_checker.sh
# Valida o sprint-checker:
# 1. SPRINT.md com has_ui:true precisa ter seção ## Visual Contract
# 2. Tokens citados em ## Visual Contract precisam existir em tokens.json
# 3. Sprint com has_forms:true ou has_error_states:true precisa citar quality/error-ux-patterns

set -u
cd "$( dirname "${BASH_SOURCE[0]}" )"

FAIL=0

# Simulador do sprint-checker.
# Recebe path do fixture (com SPRINT.md + tokens.json) e emite PASS ou BLOCK com razões.
sprint_check() {
  local fixture_dir="$1"
  local sprint="$fixture_dir/SPRINT.md"
  local tokens="$fixture_dir/tokens.json"
  local violations=()
  
  if [[ ! -f "$sprint" ]]; then
    echo "BLOCK"
    echo "reason: sprint_file_missing"
    return
  fi
  
  # Extrai front-matter (linhas entre --- e ---)
  local has_ui=false
  local has_forms=false
  local has_error_states=false
  local has_motion=false
  local touches_shared=false
  local locale=""
  
  in_frontmatter=0
  while IFS= read -r line; do
    if [[ "$line" == "---" ]]; then
      if [[ $in_frontmatter -eq 0 ]]; then
        in_frontmatter=1
      else
        break
      fi
      continue
    fi
    if [[ $in_frontmatter -eq 1 ]]; then
      [[ "$line" =~ ^has_ui:[[:space:]]*(true|false) ]] && has_ui="${BASH_REMATCH[1]}"
      [[ "$line" =~ ^has_forms:[[:space:]]*(true|false) ]] && has_forms="${BASH_REMATCH[1]}"
      [[ "$line" =~ ^has_error_states:[[:space:]]*(true|false) ]] && has_error_states="${BASH_REMATCH[1]}"
      [[ "$line" =~ ^has_non_trivial_motion:[[:space:]]*(true|false) ]] && has_motion="${BASH_REMATCH[1]}"
      [[ "$line" =~ ^touches_shared_components:[[:space:]]*(true|false) ]] && touches_shared="${BASH_REMATCH[1]}"
      [[ "$line" =~ ^locale:[[:space:]]*([a-zA-Z-]+) ]] && locale="${BASH_REMATCH[1]}"
    fi
  done < "$sprint"
  
  # Regra 1: has_ui:true exige seção "## Visual Contract"
  if [[ "$has_ui" == "true" ]]; then
    if ! grep -q "^## Visual Contract" "$sprint"; then
      violations+=("missing_section:Visual Contract")
    fi
    
    # Regra 2: tokens citados precisam existir em tokens.json
    if [[ -f "$tokens" ]] && grep -q "^## Visual Contract" "$sprint"; then
      # Extrai linhas dentro da seção ## Visual Contract (até próxima ##)
      # Depois grep para capturar tokens em backticks
      local cited_tokens
      cited_tokens=$(
        sed -n '/^## Visual Contract/,/^## /p' "$sprint" \
          | grep -oE '`[a-z]+(\.[a-zA-Z0-9_-]+)+`' \
          | tr -d '`' \
          | sort -u
      )
      
      while IFS= read -r tok; do
        [[ -z "$tok" ]] && continue
        if ! python3 -c "
import json, sys
tokens = json.load(open('$tokens'))
path = '$tok'.split('.')
node = tokens
try:
    for p in path:
        node = node[p]
    if isinstance(node, dict) and 'value' not in node:
        sys.exit(1)
    sys.exit(0)
except (KeyError, TypeError):
    sys.exit(1)
" 2>/dev/null; then
          violations+=("token_not_in_design_system:$tok")
        fi
      done <<< "$cited_tokens"
    fi
  fi
  
  # Regra 3: has_forms OU has_error_states exige citação de quality/error-ux-patterns
  if [[ "$has_forms" == "true" || "$has_error_states" == "true" ]]; then
    if ! grep -q "quality/error-ux-patterns" "$sprint"; then
      violations+=("missing_required_skill:quality/error-ux-patterns")
    fi
  fi
  
  # Regra 4: touches_shared exige product/visual-regression-testing
  if [[ "$touches_shared" == "true" ]]; then
    if ! grep -q "product/visual-regression-testing" "$sprint"; then
      violations+=("missing_required_skill:product/visual-regression-testing")
    fi
  fi
  
  # Regra 5: has_motion exige product/micro-animations-delight
  if [[ "$has_motion" == "true" ]]; then
    if ! grep -q "product/micro-animations-delight" "$sprint"; then
      violations+=("missing_required_skill:product/micro-animations-delight")
    fi
  fi
  
  # Regra 6: has_ui:true + locale:pt-BR exige br/ux-copywriting-ptbr
  if [[ "$has_ui" == "true" && "$locale" == "pt-BR" ]]; then
    if ! grep -q "br/ux-copywriting-ptbr" "$sprint"; then
      violations+=("missing_required_skill:br/ux-copywriting-ptbr")
    fi
  fi
  
  # Regra 7: has_ui:true sempre exige quality/accessibility-pro
  if [[ "$has_ui" == "true" ]]; then
    if ! grep -q "quality/accessibility-pro" "$sprint"; then
      violations+=("missing_required_skill:quality/accessibility-pro")
    fi
  fi
  
  if [[ ${#violations[@]} -eq 0 ]]; then
    echo "PASS"
  else
    echo "BLOCK"
    for v in "${violations[@]}"; do
      echo "reason: $v"
    done
  fi
}

check_fixture() {
  local name="$1"
  local dir="fixtures/$name"
  local expected="$dir/expected.txt"
  
  local actual
  actual=$(sprint_check "$dir")
  
  local expected_verdict
  expected_verdict=$(head -n1 "$expected" | tr -d ' \n')
  local actual_verdict
  actual_verdict=$(echo "$actual" | head -n1 | tr -d ' \n')
  
  if [[ "$expected_verdict" != "$actual_verdict" ]]; then
    echo "FAIL: $name — verdict esperado '$expected_verdict', obtido '$actual_verdict'"
    echo "  actual:"
    echo "$actual" | sed 's/^/    /'
    FAIL=$((FAIL + 1))
    return
  fi
  
  # Confere que todas as razões esperadas aparecem
  local missing=""
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    [[ "$line" == "$expected_verdict" ]] && continue
    if ! echo "$actual" | grep -qF "$line"; then
      missing="${missing}\n    esperado faltando: $line"
    fi
  done < "$expected"
  
  if [[ -n "$missing" ]]; then
    echo -e "FAIL: $name — razões não aparecem no output:$missing"
    echo "  actual:"
    echo "$actual" | sed 's/^/    /'
    FAIL=$((FAIL + 1))
  else
    echo "OK: $name"
  fi
}

check_fixture "good-sprint"
check_fixture "bad-sprint-no-visual-contract"
check_fixture "bad-sprint-unknown-token"

if [[ $FAIL -eq 0 ]]; then
  echo "sprint-checker smoke: 0 failures"
  exit 0
else
  echo "sprint-checker smoke: $FAIL failures"
  exit 1
fi
