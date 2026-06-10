#!/usr/bin/env bash
# tests/framework/test_wireframe_fidelity.sh
# Cadeia de fidelidade de wireframe (v0.9.7).
#
# Antes: o ingestor lia o DOM do wireframe (DECISION-49), mas o ui-phase não
# era obrigado a consultá-lo ao gerar o UI-SPEC, e nenhum checker validava a
# tela construída contra ele — fidelidade dependia de boa vontade do agente.
# Esta suite prova que cada elo da cadeia agora existe e funciona:
# extração mecânica → obrigação no ui-phase → Dimension 7 → evidência no Gate 8.
set -u
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
GSD_TOOLS="$ROOT/.claude/get-shit-done/bin/gsd-tools.cjs"

TMPDIR_T=$(mktemp -d)
trap 'rm -rf "$TMPDIR_T"' EXIT

FAIL=0
check() {
  if eval "$2"; then
    echo "  ✓ $1"
  else
    echo "  ✗ FALHOU: $1"
    FAIL=1
  fi
}

cat > "$TMPDIR_T/tela.html" << 'EOF'
<!DOCTYPE html><html><head><style>.btn{background:#2563eb}</style></head><body>
<header><h1>Painel</h1><nav><a href="/dashboard">Dashboard</a><a href="/config">Config</a></nav></header>
<main><h2>Nova Entrada</h2>
<form><input type="email" name="email" placeholder="Seu email"><select name="tipo"></select><button type="submit">Enviar</button></form>
<section class="empty-state">Nenhum item</section>
<div class="skeleton"></div>
<button aria-label="Exportar">Exportar</button>
</main><footer><a href="/sobre">Sobre</a></footer>
</body></html>
EOF

wf() { node "$GSD_TOOLS" wireframe-contract "$TMPDIR_T/tela.html"; }

echo "[wireframe] Extração estrutural do DOM"
check "regiões detectadas (header/nav/main/footer)" "wf | grep -q '\"header\"' && wf | grep -q '\"footer\"'"
check "headings com texto literal" "wf | grep -q 'Nova Entrada'"
check "botões com texto" "wf | grep -q 'Enviar' && wf | grep -q 'Exportar'"
check "links com destino (nav_targets)" "wf | grep -q '/dashboard' && wf | grep -q '/sobre'"
check "inputs de form por name" "wf | grep -q '\"email\"' && wf | grep -q '\"tipo\"'"
check "estados detectados (loading+empty)" "wf | grep -q 'loading' && wf | grep -q 'empty'"
check "cores candidatas a token" "wf | grep -q '#2563eb'"
check "checklist_size > 0" "wf | grep -qE '\"checklist_size\": [1-9]'"

echo "[wireframe] Robustez"
check "extensão não suportada (.png) recusa com explicação" "! node \"$GSD_TOOLS\" wireframe-contract /tmp/x.png > /dev/null 2>&1"
echo '<div><p>sem nada interativo</p></div>' > "$TMPDIR_T/vazio.html"
check "wireframe sem interativos não quebra" "node \"$GSD_TOOLS\" wireframe-contract \"$TMPDIR_T/vazio.html\" | grep -q 'checklist_size'"

echo "[wireframe] Cadeia de enforcement existe em cada elo"
check "ui-phase tem passo 2.5 (fonte de verdade)" "grep -q 'Wireframe como fonte de verdade' '$ROOT/.claude/get-shit-done/workflows/ui-phase.md'"
check "ui-phase exige wireframe_source por tela" "grep -q 'wireframe_source' '$ROOT/.claude/get-shit-done/workflows/ui-phase.md'"
check "ui-phase exige bloco deviations" "grep -q 'deviations' '$ROOT/.claude/get-shit-done/workflows/ui-phase.md'"
check "ui-checker tem Dimension 7" "grep -q 'Dimension 7: Wireframe Fidelity' '$ROOT/.claude/agents/gsd-ui-checker.md'"
check "Dimension 7 manda rodar o contrato (não confiar em auto-relato)" "grep -q 'do NOT trust' '$ROOT/.claude/agents/gsd-ui-checker.md'"
check "Dimension 7 bloqueia omissão silenciosa" "grep -A20 'Dimension 7' '$ROOT/.claude/agents/gsd-ui-checker.md' | grep -qi 'silent'"
check "verify-phase (Gate 8) confere contrato no código construído" "grep -q 'wireframe-contract' '$ROOT/.claude/get-shit-done/workflows/verify-phase.md'"
check "tabela de veredito do checker tem a linha 7" "grep -q '7 Wireframe Fidelity' '$ROOT/.claude/agents/gsd-ui-checker.md'"

exit $FAIL
