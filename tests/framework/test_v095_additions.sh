#!/usr/bin/env bash
# tests/framework/test_v095_additions.sh
# Smoke test das adições da v0.9.5: skills novas, agente, command, integração.
set -u
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
cd "$ROOT"

FAIL=0
check() {
  if eval "$2"; then
    echo "  ✓ $1"
  else
    echo "  ✗ FALHOU: $1"
    FAIL=1
  fi
}

echo "[v0.9.5] Skills novas existem com SKILL.md + triggers.yaml"
for sk in domain/fastapi-production-patterns domain/github-actions-ci ux-advanced/data-tables-ux ux-advanced/search-filter-ux meta/parallel-orchestration; do
  check "$sk/SKILL.md" "[ -s .claude/skills/$sk/SKILL.md ]"
  check "$sk/triggers.yaml" "[ -s .claude/skills/$sk/triggers.yaml ]"
done

echo "[v0.9.5] Agente e command novos existem"
check "gsd-wave-dispatcher agent" "[ -s .claude/agents/gsd-wave-dispatcher.md ]"
check "/gsd:go command" "[ -s .claude/commands/gsd/go.md ]"
check "go workflow" "[ -s .claude/get-shit-done/workflows/go.md ]"

echo "[v0.9.5] Referência fantasma gsd-task-executor eliminada"
check "sem gsd-task-executor em workflows" "! grep -rq 'gsd-task-executor' .claude/"

echo "[v0.9.5] Integração: execute-phase conhece wave-dispatcher"
check "execute-phase referencia wave-dispatcher" "grep -q 'gsd-wave-dispatcher' .claude/get-shit-done/workflows/execute-phase.md"
check "autopilot lê parallel-hint" "grep -q 'parallel-hint' .claude/get-shit-done/workflows/autopilot.md"
check "roadmapper grava parallel-hint" "grep -q 'parallel-hint' .claude/agents/gsd-roadmapper.md"

echo "[v0.9.5] plan-checker reconhece clause config"
check "plan-checker tem clause config:" "grep -q 'config: X' .claude/agents/gsd-plan-checker.md"

echo "[v0.9.5] config template é JSON válido com wave_dispatcher"
check "config template válido" "node -e 'JSON.parse(require(\"fs\").readFileSync(\".claude/get-shit-done/templates/config.json\"))' 2>/dev/null"
check "wave_dispatcher no template" "grep -q 'wave_dispatcher' .claude/get-shit-done/templates/config.json"

echo "[v0.9.5] Gate 8 — Senior Quality Bar"
check "skill senior-quality-bar existe" "[ -s .claude/skills/quality/senior-quality-bar/SKILL.md ]"
check "skill senior-quality-bar triggers" "[ -s .claude/skills/quality/senior-quality-bar/triggers.yaml ]"
check "Gate 8 no gates-v3" "grep -q 'Gate 8' .claude/get-shit-done/references/gates-v3.md"
check "Gate 8 no CLAUDE.md" "grep -q 'Senior Quality Bar' CLAUDE.md"
check "verify-phase invoca Gate 8" "grep -q 'gate_8_senior_quality_bar' .claude/get-shit-done/workflows/verify-phase.md"

echo "[v0.9.5] Framework-telemetry (mede o framework, não o projeto)"
check "collect-framework-telemetry.sh existe" "[ -s bin/collect-framework-telemetry.sh ]"
check "collect-framework-telemetry sintaxe OK" "bash -n bin/collect-framework-telemetry.sh"
check "hook dispara framework-telemetry" "grep -q 'collect-framework-telemetry' .claude/hooks/gsd-metrics-trigger.js"

echo "[v0.9.5] Portabilidade — sem path Windows hardcoded"
check "zero C:/Projetos no .claude" "[ \$(grep -rl 'C:/Projetos' .claude/ 2>/dev/null | wc -l) -eq 0 ]"

echo "[v0.9.5] Contagem real de skills = 73 (72 + senior-quality-bar)"
N=$(find .claude/skills -name SKILL.md | wc -l | tr -d ' ')
check "73 SKILL.md (achou $N)" "[ \"$N\" = \"73\" ]"

if [ "$FAIL" = "0" ]; then
  echo "v0.9.5 additions: OK"
  exit 0
else
  echo "v0.9.5 additions: FALHAS detectadas"
  exit 1
fi
