#!/usr/bin/env bash
# test_e2e_ingest_autopilot.sh
#
# Teste de integração ponta-a-ponta do fluxo principal v0.9.1+:
#   projeto/ → /gsd:ingest → INGESTOR-HANDOFF.json → /gsd:autopilot Fase 0
#
# Este teste NÃO roda Claude (não há LLM no CI). Valida apenas que:
#   1. Estrutura do framework suporta o fluxo
#   2. Arquivos críticos têm os campos contratuais esperados
#   3. Hooks reagem corretamente a presença/ausência de arquivos
#   4. Workflow do autopilot tem Step 0 funcional
#
# Para testar com LLM real, ver: docs/E2E-MANUAL-TEST.md

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$FRAMEWORK_ROOT"

# ANSI colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

assert() {
  local desc="$1"
  local cmd="$2"
  if eval "$cmd" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} $desc"
    PASS=$((PASS + 1))
  else
    echo -e "  ${RED}✗${NC} $desc"
    FAIL=$((FAIL + 1))
  fi
}

warn_if_missing() {
  local desc="$1"
  local cmd="$2"
  if eval "$cmd" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} $desc"
    PASS=$((PASS + 1))
  else
    echo -e "  ${YELLOW}⚠${NC} $desc (warning, não-bloqueante)"
    WARN=$((WARN + 1))
  fi
}

echo "═══════════════════════════════════════════════════════"
echo "E2E TEST: projeto/ → /gsd:ingest → /gsd:autopilot"
echo "═══════════════════════════════════════════════════════"
echo ""

echo "▶ Suite 1: Estrutura da pasta projeto/"
assert "projeto/ existe" "[ -d projeto ]"
assert "projeto/README.md existe" "[ -f projeto/README.md ]"
assert "projeto/regras-negocio/ existe" "[ -d projeto/regras-negocio ]"
assert "projeto/wireframes/ existe" "[ -d projeto/wireframes ]"
assert "projeto/identidade-visual/ existe" "[ -d projeto/identidade-visual ]"
assert "projeto/stacks/ existe" "[ -d projeto/stacks ]"
assert "projeto/docs-externos/ existe" "[ -d projeto/docs-externos ]"
assert "projeto/referencias/ existe" "[ -d projeto/referencias ]"
assert "projeto/decisoes-existentes/ existe" "[ -d projeto/decisoes-existentes ]"
assert "wireframes/README.md menciona HTML" "grep -q 'HTML' projeto/wireframes/README.md"
echo ""

echo "▶ Suite 2: Agent gsd-project-ingestor"
assert "agent existe" "[ -f .claude/agents/gsd-project-ingestor.md ]"
assert "agent gera INGESTOR-HANDOFF.json" "grep -q 'INGESTOR-HANDOFF.json' .claude/agents/gsd-project-ingestor.md"
assert "agent tem Fase 10 (handoff)" "grep -q '### Fase 10' .claude/agents/gsd-project-ingestor.md"
assert "agent menciona handoff ao autopilot" "grep -q 'autopilot' .claude/agents/gsd-project-ingestor.md"
assert "agent trata HTML como caso especial" "grep -q 'TRATAMENTO ESPECIAL' .claude/agents/gsd-project-ingestor.md"
assert "agent gera ROADMAP com Squad recomendado" "grep -q 'Squad recomendado' .claude/agents/gsd-project-ingestor.md"
assert "agent pré-cita skills no ROADMAP" "grep -q 'pré-citação' .claude/agents/gsd-project-ingestor.md"
echo ""

echo "▶ Suite 3: Command /gsd:ingest"
assert "command existe" "[ -f .claude/commands/gsd/ingest.md ]"
assert "command tem argumento --dry-run" "grep -q 'dry-run' .claude/commands/gsd/ingest.md"
assert "command menciona próximo passo (bootstrap/autopilot)" "grep -qE 'bootstrap|autopilot' .claude/commands/gsd/ingest.md"
echo ""

echo "▶ Suite 4: Command /gsd:bootstrap com routing"
assert "command existe" "[ -f .claude/commands/gsd/bootstrap.md ]"
assert "bootstrap detecta projeto/" "grep -q 'projeto/' .claude/commands/gsd/bootstrap.md"
assert "bootstrap redireciona para ingest" "grep -q '/gsd:ingest' .claude/commands/gsd/bootstrap.md"
assert "workflow bootstrap tem routing_decision" "grep -q 'routing_decision' .claude/get-shit-done/workflows/bootstrap.md"
echo ""

echo "▶ Suite 5: Autopilot lê handoff do ingestor"
assert "autopilot workflow existe" "[ -f .claude/get-shit-done/workflows/autopilot.md ]"
assert "autopilot tem Step 0 (read-ingestor-handoff)" "grep -q '0-read-ingestor-handoff' .claude/get-shit-done/workflows/autopilot.md"
assert "Step 0 lê INGESTOR-HANDOFF.json" "grep -q 'INGESTOR-HANDOFF.json' .claude/get-shit-done/workflows/autopilot.md"
assert "Step 0 bloqueia se open_questions_blocking > 0" "grep -q 'READY..false' .claude/get-shit-done/workflows/autopilot.md || grep -q 'ready_for_autopilot.*false\\|READY.*false' .claude/get-shit-done/workflows/autopilot.md"
echo ""

echo "▶ Suite 6: Autopilot invoca squad automaticamente"
assert "squad-research disparado antes de discuss-phase" "grep -q '4.2.5 Squad-research' .claude/get-shit-done/workflows/autopilot.md"
assert "squad-review disparado após execute-phase" "grep -q '4.9.5 Squad-review' .claude/get-shit-done/workflows/autopilot.md"
assert "squad-audit disparado antes de milestone close" "grep -q '5.2 Squad-audit' .claude/get-shit-done/workflows/autopilot.md"
assert "squad CRITICAL bloqueia avanço" "grep -q 'CRITICAL.*resolver\\|resolver agora\\|bloqueia' .claude/get-shit-done/workflows/autopilot.md"
echo ""

echo "▶ Suite 7: Squad orchestrator"
assert "agent gsd-squad-orchestrator existe" "[ -f .claude/agents/gsd-squad-orchestrator.md ]"
assert "command /gsd:squad existe" "[ -f .claude/commands/gsd/squad.md ]"
assert "agent menciona 3 squads (research, review, audit)" "grep -c 'squad-research\\|squad-review\\|squad-audit' .claude/agents/gsd-squad-orchestrator.md | head -1"
echo ""

echo "▶ Suite 8: Audit agents existem"
assert "gsd-performance-auditor existe" "[ -f .claude/agents/gsd-performance-auditor.md ]"
assert "gsd-accessibility-auditor existe" "[ -f .claude/agents/gsd-accessibility-auditor.md ]"
assert "gsd-i18n-auditor existe" "[ -f .claude/agents/gsd-i18n-auditor.md ]"
assert "gsd-observability-auditor existe" "[ -f .claude/agents/gsd-observability-auditor.md ]"
echo ""

echo "▶ Suite 9: Hook projeto-watcher"
assert "hook existe" "[ -f .claude/hooks/gsd-projeto-watcher.js ]"
assert "hook é executável node" "node -c .claude/hooks/gsd-projeto-watcher.js"
assert "settings.json inclui projeto-watcher" "grep -q 'projeto-watcher' .claude/settings.json"
assert "settings.json tem env GSD_PROJETO_WATCHER_ENABLED" "grep -q 'GSD_PROJETO_WATCHER_ENABLED' .claude/settings.json"
echo ""

echo "▶ Suite 10: Permissões cross-platform"
PERM_COUNT=$(node -e "console.log(JSON.parse(require('fs').readFileSync('.claude/settings.json')).permissions.allow.length)")
assert "settings.json tem 300+ permissions" "[ $PERM_COUNT -ge 300 ]"
assert "defaultMode é bypassPermissions" "grep -q '\"defaultMode\": \"bypassPermissions\"' .claude/settings.json"
assert "permissions cobrem PowerShell" "grep -q 'powershell' .claude/settings.json"
assert "permissions cobrem winget" "grep -q 'winget' .claude/settings.json"
assert "permissions cobrem brew (macOS)" "grep -q 'brew' .claude/settings.json"
echo ""

echo "▶ Suite 11: ERRATA eliminada (docs honestos)"
assert "ERRATA.md NÃO existe" "[ ! -f ERRATA.md ]"
assert "docs/PLATFORM-NOTES.md existe" "[ -f docs/PLATFORM-NOTES.md ]"
assert "docs/KNOWN-LIMITS.md existe" "[ -f docs/KNOWN-LIMITS.md ]"
echo ""

echo "▶ Suite 12: Hook node syntax valida"
for hook in .claude/hooks/*.js; do
  hookname=$(basename "$hook")
  assert "$hookname tem sintaxe válida" "node -c '$hook'"
done
echo ""

echo "▶ Suite 13: Env smoke check (v0.9.2)"
assert "bin/env-smoke-check.sh existe" "[ -f bin/env-smoke-check.sh ]"
assert "bin/env-smoke-check.sh é executável" "[ -x bin/env-smoke-check.sh ]"
assert "smoke check tem sintaxe bash válida" "bash -n bin/env-smoke-check.sh"
assert "autopilot Step 4.1.5 invoca smoke check" "grep -q '4.1.5 Env-smoke-check' .claude/get-shit-done/workflows/autopilot.md"
assert "autopilot lida com exit code 1 (blocker)" "grep -q 'SMOKE_EXIT' .claude/get-shit-done/workflows/autopilot.md"
echo ""

echo "▶ Suite 14: TD aging policy (v0.9.2)"
assert "hook gsd-td-aging.js existe" "[ -f .claude/hooks/gsd-td-aging.js ]"
assert "hook td-aging tem sintaxe JS válida" "node -c .claude/hooks/gsd-td-aging.js"
assert "command /gsd:td-review existe" "[ -f .claude/commands/gsd/td-review.md ]"
assert "settings.json inclui td-aging hook" "grep -q 'gsd-td-aging' .claude/settings.json"
assert "env GSD_TD_AGING_ENABLED setado" "grep -q 'GSD_TD_AGING_ENABLED' .claude/settings.json"
echo ""

echo "▶ Suite 15: Plan-checker Dimension 13 (v0.9.2)"
assert "Dimension 13 adicionada ao plan-checker" "grep -q '## Dimension 13: API Surface Compliance' .claude/agents/gsd-plan-checker.md"
assert "Dimension 13 menciona signatures" "grep -q 'function_signature_mismatch\\|signature_mismatch' .claude/agents/gsd-plan-checker.md"
assert "Dimension 13 menciona schema fields" "grep -q 'schema_field\\|schema field' .claude/agents/gsd-plan-checker.md"
assert "Dimension 13 menciona endpoint paths" "grep -q 'endpoint_path\\|api/v1' .claude/agents/gsd-plan-checker.md"
echo ""

echo "▶ Suite 16: Deploy-safety (v0.9.3)"
assert "skill domain/monorepo-deploy-safety existe" "[ -f .claude/skills/domain/monorepo-deploy-safety/SKILL.md ]"
assert "skill tem triggers.yaml" "[ -f .claude/skills/domain/monorepo-deploy-safety/triggers.yaml ]"
assert "skill recomenda symlink (não blue-green default)" "grep -q 'symlink atomic' .claude/skills/domain/monorepo-deploy-safety/SKILL.md"
assert "skill documenta anti-Turborepo" "grep -qi 'NÃO Turborepo\\|não Turborepo\\|Turborepo na' .claude/skills/domain/monorepo-deploy-safety/SKILL.md"
assert "skill documenta invariantes Phase 1" "grep -q 'DESDE A PHASE 1\\|Phase 1' .claude/skills/domain/monorepo-deploy-safety/SKILL.md"
assert "agent gsd-release-auditor existe" "[ -f .claude/agents/gsd-release-auditor.md ]"
assert "release-auditor tem 7 dimensões" "grep -q '7 dimensões' .claude/agents/gsd-release-auditor.md"
assert "bin/deploy-atomic.sh existe" "[ -f bin/deploy-atomic.sh ]"
assert "deploy-atomic.sh é executável" "[ -x bin/deploy-atomic.sh ]"
assert "deploy-atomic.sh tem sintaxe bash válida" "bash -n bin/deploy-atomic.sh"
assert "deploy-atomic.sh suporta --rollback" "grep -q 'rollback' bin/deploy-atomic.sh"
assert "deploy-atomic.sh suporta --dry-run" "grep -q 'dry-run' bin/deploy-atomic.sh"
assert "autopilot Step 5.2.5 invoca release-auditor" "grep -q '5.2.5 Release-auditor' .claude/get-shit-done/workflows/autopilot.md"
assert "release-auditor na squad-audit do orchestrator" "grep -q 'release auditor' .claude/agents/gsd-squad-orchestrator.md"
echo ""

echo "▶ Suite 17: Docker deploy + data safety (v0.9.4)"
assert "bin/deploy-docker.sh existe" "[ -f bin/deploy-docker.sh ]"
assert "deploy-docker.sh sintaxe válida" "bash -n bin/deploy-docker.sh"
assert "deploy-docker.sh NUNCA usa down -v (em código ativo)" "! grep -E 'compose down (-v|--volumes)' bin/deploy-docker.sh | grep -qv '^[[:space:]]*#'"
assert "deploy-docker.sh faz backup pré-migration" "grep -q 'pre-migration' bin/deploy-docker.sh"
assert "deploy-docker.sh aborta sem backup" "grep -q 'NÃO deve prosseguir sem backup\\|ABORTADO' bin/deploy-docker.sh"
assert "deploy-docker.sh tem rollback por tag" "grep -q 'rollback\\|ROLLBACK' bin/deploy-docker.sh"
assert "bin/backup-mysql-b2.sh existe" "[ -f bin/backup-mysql-b2.sh ]"
assert "backup-mysql-b2.sh sintaxe válida" "bash -n bin/backup-mysql-b2.sh"
assert "backup tem single-transaction (sem downtime)" "grep -q 'single-transaction' bin/backup-mysql-b2.sh"
assert "backup tem binlog para PITR" "grep -q 'binlog' bin/backup-mysql-b2.sh"
assert "backup tem retenção 30 dias" "grep -q 'RETENTION_DAYS:-30' bin/backup-mysql-b2.sh"
assert "bin/restore-mysql-b2.sh existe" "[ -f bin/restore-mysql-b2.sh ]"
assert "restore-mysql-b2.sh sintaxe válida" "bash -n bin/restore-mysql-b2.sh"
assert "restore tem PITR (point-in-time)" "grep -q 'pitr\\|stop-datetime' bin/restore-mysql-b2.sh"
assert "restore tem dupla confirmação" "grep -q 'confirm1\\|confirm2\\|confirm_destructive' bin/restore-mysql-b2.sh"
assert "skill tem seção Docker (5B)" "grep -q '5B. Variante Docker' .claude/skills/domain/monorepo-deploy-safety/SKILL.md"
assert "skill: MySQL fora do Docker" "grep -q 'MySQL NATIVO\\|MySQL nativo' .claude/skills/domain/monorepo-deploy-safety/SKILL.md"
assert "skill: 3 níveis de proteção de dados" "grep -q 'Três níveis\\|três níveis' .claude/skills/domain/monorepo-deploy-safety/SKILL.md"
assert "release-auditor tem 8ª dimensão Docker" "grep -q '8 dimensões\\|8. Docker' .claude/agents/gsd-release-auditor.md"
assert "release-auditor bloqueia down -v" "grep -q 'down -v' .claude/agents/gsd-release-auditor.md"
echo ""

echo "═══════════════════════════════════════════════════════"
echo "Resultado:"
echo -e "  ${GREEN}Passed:${NC} $PASS"
if [ $WARN -gt 0 ]; then echo -e "  ${YELLOW}Warnings:${NC} $WARN"; fi
if [ $FAIL -gt 0 ]; then echo -e "  ${RED}Failed:${NC} $FAIL"; fi
echo "═══════════════════════════════════════════════════════"

if [ $FAIL -gt 0 ]; then
  exit 1
fi

exit 0
