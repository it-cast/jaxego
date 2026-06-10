#!/usr/bin/env bash
# gsd-phase-transition-guard.sh
#
# Hook bloqueante disparado antes de transição entre phases.
# Garante que phase atual está COMPLETA (todos artefatos canônicos presentes)
# antes de avançar.
#
# Resolve bug v0.4.1: autopilot pulava auto-retro entre phases.
#
# Trigger: PreToolUse quando comando inicia phase nova
# Bloqueia se: phase atual não tem todos artefatos esperados

set -euo pipefail

# Identificar diretório do projeto
PROJECT_ROOT="${CLAUDE_PROJECT_ROOT:-$(pwd)}"
cd "$PROJECT_ROOT"

# Sair silencioso se não é projeto gsd-framework
if [ ! -d ".planning" ] || [ ! -f ".planning/STATE.md" ]; then
  exit 0
fi

# Identificar comando que está sendo executado (via env var do Claude Code)
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

# Detectar comandos que iniciam phase nova
INITIATING_PATTERNS=(
  "gsd-discuss-phase"
  "gsd-plan-phase"
  "gsd-execute-phase"
  "gsd-autopilot.*--from"
)

is_phase_transition=false
for pattern in "${INITIATING_PATTERNS[@]}"; do
  if echo "$TOOL_INPUT" | grep -qE "$pattern"; then
    is_phase_transition=true
    break
  fi
done

if [ "$is_phase_transition" = "false" ]; then
  exit 0
fi

# Extrair número da phase alvo
TARGET_PHASE=$(echo "$TOOL_INPUT" | grep -oE '(--from |gsd-[a-z-]+phase )([0-9]+\.?[0-9]*)' | tail -1 | grep -oE '[0-9]+\.?[0-9]*')

if [ -z "$TARGET_PHASE" ]; then
  # Não conseguiu identificar phase, deixa passar
  exit 0
fi

# Identificar phase atual (a phase imediatamente anterior à target)
CURRENT_PHASE=$(node -e "
const target = parseFloat('$TARGET_PHASE');
if (target <= 1) { console.log(''); process.exit(0); }
console.log(Math.floor(target - 1));
" 2>/dev/null || echo "")

if [ -z "$CURRENT_PHASE" ]; then
  exit 0
fi

# Verificar phase anterior tem todos os artefatos esperados
PHASE_DIR=$(find .planning/phases -maxdepth 1 -type d -name "${CURRENT_PHASE}-*" 2>/dev/null | head -1)

if [ -z "$PHASE_DIR" ]; then
  # Phase anterior nem existe, primeira phase do projeto, ok
  exit 0
fi

# Lista de artefatos sempre obrigatórios
REQUIRED_ARTIFACTS=(
  "${PHASE_DIR}/${CURRENT_PHASE}-CONTEXT.md"
  "${PHASE_DIR}/${CURRENT_PHASE}-PLAN.md"
  "${PHASE_DIR}/${CURRENT_PHASE}-EXECUTION-LOG.md"
  "${PHASE_DIR}/${CURRENT_PHASE}-VERIFICATION.md"
  ".planning/retros/phase-${CURRENT_PHASE}.md"
)

MISSING_ARTIFACTS=()
for artifact in "${REQUIRED_ARTIFACTS[@]}"; do
  if [ ! -f "$artifact" ]; then
    MISSING_ARTIFACTS+=("$artifact")
  fi
done

# Gate 8 (Senior Quality Bar) — enforcement por código (v0.9.6).
# A phase anterior só libera transição com QUALITY-BAR.md presente,
# zero FAIL-BLOCK aberto e FAIL-DEBT contabilizado em TECH-DEBT.md.
GSD_TOOLS=".claude/get-shit-done/bin/gsd-tools.cjs"
if [ "${GSD_SKIP_TRANSITION_GUARD:-}" != "true" ] && [ -f "$GSD_TOOLS" ]; then
  QB_RESULT=$(node "$GSD_TOOLS" verify quality-bar "$CURRENT_PHASE" 2>/dev/null || echo '{"passed":false}')
  QB_PASSED=$(echo "$QB_RESULT" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{try{process.stdout.write(JSON.parse(d).passed===true?'1':'0')}catch{process.stdout.write('0')}})" 2>/dev/null)
  if [ "$QB_PASSED" != "1" ]; then
    cat >&2 << GATE8_EOF

╔══════════════════════════════════════════════════════════════════╗
║  ⛔ GATE 8 (SENIOR QUALITY BAR) — BLOQUEIO DE TRANSIÇÃO          ║
╚══════════════════════════════════════════════════════════════════╝

Phase ${CURRENT_PHASE} não passou no Gate 8. Detalhes:

GATE8_EOF
    echo "$QB_RESULT" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{try{const r=JSON.parse(d);(r.errors||[]).forEach(e=>console.error('  '+e));if(r.hint)console.error('  → '+r.hint)}catch{}})" >&2

    cat >&2 << GATE8_EOF

Para resolver:
  1. /gsd:verify-phase ${CURRENT_PHASE}   # gera/atualiza o QUALITY-BAR.md
  2. Corrija FAIL-BLOCKs (marque [RESOLVIDO] na linha após corrigir)
  3. Registre FAIL-DEBTs em .planning/TECH-DEBT.md citando "Phase ${CURRENT_PHASE}"

Override consciente (registrado): export GSD_SKIP_TRANSITION_GUARD=true
e documente a razão em .planning/DECISIONS.md.

GATE8_EOF
    exit 1
  fi
fi

# Se algum artefato faltando, BLOQUEAR transição
if [ ${#MISSING_ARTIFACTS[@]} -gt 0 ]; then
  cat >&2 << ERROR_EOF

╔══════════════════════════════════════════════════════════════════╗
║  ⚠ BLOQUEIO DE TRANSIÇÃO DE PHASE                                ║
╚══════════════════════════════════════════════════════════════════╝

Tentando avançar para Phase ${TARGET_PHASE}, mas Phase ${CURRENT_PHASE} está INCOMPLETA.

Artefatos faltando:
ERROR_EOF
  for missing in "${MISSING_ARTIFACTS[@]}"; do
    echo "  ✗ ${missing#$PROJECT_ROOT/}" >&2
  done

  cat >&2 << ERROR_EOF

Para resolver:
  1. Se PHASE-${CURRENT_PHASE} está realmente incompleta, complete os passos faltantes:
     /gsd-verify-work ${CURRENT_PHASE}      # se VERIFICATION.md falta
     /gsd-recover-retros --phase ${CURRENT_PHASE}  # se retro falta

  2. Se você intencionalmente quer pular essa validação:
     export GSD_SKIP_TRANSITION_GUARD=true
     # Ou adicione --skip-transition-guard ao comando

  3. Após resolver, rode novamente o comando.

Bloqueio é proposital: evita milestones aparentemente "completos"
mas com retros perdidas (bug v0.4.1).

ERROR_EOF
  exit 1
fi

# Tudo ok, deixa passar
exit 0
