#!/usr/bin/env bash
# tests/framework/test_quality_bar_gate.sh
# Gate 8 enforcement por código (v0.9.6): gsd-tools verify quality-bar + hook.
#
# Antes da v0.9.6 o Gate 8 era prosa em verify-phase.md — "gate citado ≠ gate
# executado". Esta suite prova que o enforcement agora é script, cobrindo os
# 4 cenários: arquivo ausente, FAIL-BLOCK aberto, FAIL-DEBT não contabilizado,
# e phase limpa.
set -u
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
GSD_TOOLS="$ROOT/.claude/get-shit-done/bin/gsd-tools.cjs"

FAIL=0
check() {
  if eval "$2"; then
    echo "  ✓ $1"
  else
    echo "  ✗ FALHOU: $1"
    FAIL=1
  fi
}

# Sandbox de projeto fake
SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT
mkdir -p "$SANDBOX/.planning/phases/01-exemplo"
echo "# STATE" > "$SANDBOX/.planning/STATE.md"

qb() { node "$GSD_TOOLS" verify quality-bar 1 --cwd "$SANDBOX" 2>/dev/null; }
passed() { qb | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{try{process.stdout.write(JSON.parse(d).passed===true?'1':'0')}catch{process.stdout.write('0')}})"; }

echo "[gate8] Cenário 1 — QUALITY-BAR.md ausente bloqueia"
check "passed=false sem arquivo" "[ \"$(passed)\" = '0' ]"
check "erro menciona ausência" "qb | grep -q 'ausente'"

echo "[gate8] Cenário 2 — FAIL-BLOCK aberto bloqueia"
cat > "$SANDBOX/.planning/phases/01-exemplo/01-QUALITY-BAR.md" << 'EOF'
# Quality Bar — Phase 01
- A1 correção: PASS
- B1 segredos no repo: FAIL-BLOCK — .env commitado
- C2 rollback: N/A
EOF
check "passed=false com FAIL-BLOCK" "[ \"$(passed)\" = '0' ]"
check "erro lista o FAIL-BLOCK" "qb | grep -q 'FAIL-BLOCK aberto'"

echo "[gate8] Cenário 3 — FAIL-BLOCK [RESOLVIDO] libera, FAIL-DEBT sem TECH-DEBT bloqueia"
cat > "$SANDBOX/.planning/phases/01-exemplo/01-QUALITY-BAR.md" << 'EOF'
# Quality Bar — Phase 01
- A1 correção: PASS
- B1 segredos: FAIL-BLOCK [RESOLVIDO] — .env removido, credencial rotacionada
- B3 N+1: FAIL-DEBT (urgency: high)
EOF
check "passed=false com FAIL-DEBT não contabilizado" "[ \"$(passed)\" = '0' ]"
check "erro menciona TECH-DEBT" "qb | grep -q 'TECH-DEBT'"

echo "[gate8] Cenário 4 — tudo contabilizado passa"
echo "## TD-001 — N+1 em lista (Phase 01, urgency high)" > "$SANDBOX/.planning/TECH-DEBT.md"
check "passed=true quando limpo" "[ \"$(passed)\" = '1' ]"

echo "[gate8] Cenário 5 — arquivo vazio/template não conta como gate avaliado"
cat > "$SANDBOX/.planning/phases/01-exemplo/01-QUALITY-BAR.md" << 'EOF'
# Quality Bar — Phase 01
(preencher)
EOF
check "passed=false com QUALITY-BAR vazio" "[ \"$(passed)\" = '0' ]"

echo "[gate8] Integração — hook de transição chama o check"
check "hook referencia verify quality-bar" "grep -q 'verify quality-bar' '$ROOT/.claude/hooks/gsd-phase-transition-guard.sh'"
check "hook tem sintaxe bash válida" "bash -n '$ROOT/.claude/hooks/gsd-phase-transition-guard.sh'"
check "workflow verify-phase exige validação por script" "grep -q 'verify quality-bar' '$ROOT/.claude/get-shit-done/workflows/verify-phase.md'"

exit $FAIL
