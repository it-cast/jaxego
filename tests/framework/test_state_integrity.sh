#!/usr/bin/env bash
# tests/framework/test_state_integrity.sh
# Testes para o bug multi-milestone (v0.8.0)
#
# Cenário: projeto Rota Certa v1.1 — STATE.md fica corrompido
# para "milestone: v1.0 / status: completed" mesmo com v1.1 in_progress.
# Causa: getMilestoneInfo() pegava v1.0 do ROADMAP em vez de v1.1 in_progress
# do MILESTONES.md.
#
# Fix v0.8.0: getMilestoneInfo agora consulta MILESTONES.md PRIMEIRO,
# antes de cair em ROADMAP.md heuristics.

set -u
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FRAMEWORK_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

GREEN=$(printf '\033[0;32m')
RED=$(printf '\033[0;31m')
RESET=$(printf '\033[0m')

PASS=0
FAIL=0

assert_eq() {
  local actual="$1"
  local expected="$2"
  local msg="$3"
  if [[ "$actual" == "$expected" ]]; then
    echo "  ${GREEN}✓${RESET} $msg"
    PASS=$((PASS + 1))
  else
    echo "  ${RED}✗${RESET} $msg"
    echo "       expected: $expected"
    echo "       got:      $actual"
    FAIL=$((FAIL + 1))
  fi
}

# ─── Setup: temp project ──────────────────────────────────────────────────
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT
cd "$TMPDIR"

mkdir -p .planning/phases

# ROADMAP.md com 2 milestones (v1.0 shipped, v1.1 atual)
cat > .planning/ROADMAP.md << 'EOF'
# Roadmap

## Roadmap v1.0: MVP — Phases 1-5
✅ Shipped 2026-04-30

### Phase 1: Foundation
### Phase 2: Cadastros
### Phase 3: Núcleo
### Phase 4: Financeiro
### Phase 5: Integração

## Roadmap v1.1: Mobile + KYC — Phases 6-9
🚧 In progress

### Phase 6: Mobile Auth
### Phase 7: Delivery Mobile
### Phase 8: KYC + Score
### Phase 9: Release CI
EOF

# MILESTONES.md com v1.0 completed e v1.1 in_progress
cat > .planning/MILESTONES.md << 'EOF'
# MILESTONES

| ID | Nome | Release | Phases | Critério | Status |
|----|------|---------|--------|----------|--------|
| MS-01 | v1.0 MVP | 2026-04-30 | 1-5 | Pipeline funcional | completed ✅ |
| MS-02 | v1.1 Mobile | 2026-07-15 | 6-9 | App publicado | in_progress ⏳ |
EOF

# STATE.md corrompido (cenário do bug — sessão anterior travou em v1.0)
cat > .planning/STATE.md << 'EOF'
---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: MVP
status: completed
progress:
  total_phases: 5
  completed_phases: 5
  total_plans: 12
  completed_plans: 12
  percent: 100
---

# STATE — Current Execution State

## Current Position

- Status: MS-02 iniciado — Phase 7 in_progress
- Last activity: 2026-05-08
EOF

# Phases 1-9 (com fases v1.0 e v1.1)
for n in 1 2 3 4 5 6 7 8 9; do
  mkdir -p ".planning/phases/0$n-test"
  touch ".planning/phases/0$n-test/0$n-PLAN.md"
  if (( n <= 5 )); then
    touch ".planning/phases/0$n-test/0$n-SUMMARY.md"
  fi
done

# ─── Test 1: getMilestoneInfo deve retornar v1.1 (não v1.0 do STATE.md) ────
echo ""
echo "=== Test 1: getMilestoneInfo prioriza MILESTONES.md ==="

OUTPUT=$(node -e "
const { getMilestoneInfo } = require('$FRAMEWORK_ROOT/.claude/get-shit-done/bin/lib/core.cjs');
const info = getMilestoneInfo('$TMPDIR');
console.log(info.version);
")

assert_eq "$OUTPUT" "v1.1" "version detectada do MILESTONES.md (não v1.0 do STATE.md corrompido)"

# ─── Test 2: getMilestoneInfo funciona sem MILESTONES.md (fallback ROADMAP) ─
echo ""
echo "=== Test 2: Fallback para ROADMAP quando MILESTONES.md não existe ==="

rm .planning/MILESTONES.md

OUTPUT2=$(node -e "
const { getMilestoneInfo } = require('$FRAMEWORK_ROOT/.claude/get-shit-done/bin/lib/core.cjs');
const info = getMilestoneInfo('$TMPDIR');
console.log(info.version);
")

assert_eq "$OUTPUT2" "v1.1" "version detectada do ROADMAP 🚧 marker"

# ─── Test 3: Sem nenhum dos 2 → fallback v1.0 (default seguro) ─────────────
echo ""
echo "=== Test 3: Sem ROADMAP nem MILESTONES → fallback v1.0 ==="

rm .planning/ROADMAP.md

OUTPUT3=$(node -e "
const { getMilestoneInfo } = require('$FRAMEWORK_ROOT/.claude/get-shit-done/bin/lib/core.cjs');
const info = getMilestoneInfo('$TMPDIR');
console.log(info.version);
")

assert_eq "$OUTPUT3" "v1.0" "fallback default v1.0 quando sem fontes"

# ─── Resumo ────────────────────────────────────────────────────────────────
echo ""
echo "─────────────────────────────────"
if (( FAIL == 0 )); then
  echo "${GREEN}✓ $PASS/$((PASS + FAIL)) passed${RESET}"
  exit 0
else
  echo "${RED}✗ $FAIL/$((PASS + FAIL)) failed${RESET}"
  exit 1
fi
