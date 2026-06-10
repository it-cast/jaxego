#!/usr/bin/env bash
# tests/framework/test_structure.sh
# Valida que a estrutura essencial do framework está íntegra

set -e
cd "$( dirname "${BASH_SOURCE[0]}" )/../.."

FAILED=0
assert_file() {
  if [[ ! -f "$1" ]]; then
    echo "FAIL: arquivo faltando: $1"
    FAILED=$((FAILED + 1))
  fi
}

assert_dir() {
  if [[ ! -d "$1" ]]; then
    echo "FAIL: diretório faltando: $1"
    FAILED=$((FAILED + 1))
  fi
}

assert_file_nonempty() {
  if [[ ! -s "$1" ]]; then
    echo "FAIL: arquivo vazio ou ausente: $1"
    FAILED=$((FAILED + 1))
  fi
}

# Root files
assert_file "CLAUDE.md"
assert_file "README.md"
assert_file "FRAMEWORK-STATUS.md"

# Core directories
assert_dir ".claude/get-shit-done/workflows"
assert_dir ".claude/get-shit-done/references"
assert_dir ".claude/skills"
assert_dir ".planning"
assert_dir "specs"
assert_dir "docs"

# Workflows esperados
for wf in plan-phase execute-phase ui-phase bootstrap reconcile-state; do
  assert_file ".claude/get-shit-done/workflows/${wf}.md"
done

# Skills index
assert_file ".claude/skills/SKILLS_INDEX.md"

# Specs
for spec in project stack database rules; do
  assert_file "specs/${spec}.yaml"
done

# Skills expandidas (não podem estar vazias — devem ter conteúdo substantivo > 1KB)
# v0.3.0: 44 skills (era 14 em v0.2.x)
for skill in \
  quality/performance-web-vitals \
  quality/error-ux-patterns \
  quality/observability-production \
  quality/accessibility-pro \
  quality/i18n-ready-architecture \
  product/api-design-contracts \
  product/visual-regression-testing \
  product/component-library-governance \
  product/micro-animations-delight \
  mobile/offline-first \
  mobile/push-notifications-architecture \
  br/brazilian-forms \
  br/ux-copywriting-ptbr \
  br/lgpd-compliance \
  ux-advanced/chat-ux-patterns \
  ux-advanced/dark-mode-theming \
  ux-advanced/design-tokens-system \
  ux-advanced/empty-states-polish \
  ux-advanced/file-upload-ux \
  ux-advanced/form-ux-mastery \
  ux-advanced/gesture-touch-patterns \
  ux-advanced/motion-design-patterns \
  ux-advanced/onboarding-patterns \
  ux-advanced/payment-checkout-ux \
  ux-advanced/responsive-breakpoint-strategy \
  ux-advanced/saas-dashboard-patterns \
  ux-advanced/trust-safety-ux \
  ux-advanced/ui-input-rich-patterns \
  domain/angular-material-patterns \
  domain/docker-production-ready \
  domain/ionic-patterns \
  domain/llm-integration-patterns \
  domain/mysql-schema-design \
  domain/safe2pay-escrow-br \
  meta/design-to-code \
  meta/orchestration-decision-tree \
  meta/project-kickoff-interview \
  meta/stack-advisor \
  owasp-security \
  prompt-engineering \
  spartan-ai-toolkit \
  systematic-debugging \
  ui-ux-pro-max \
  webapp-testing
do
  path=".claude/skills/${skill}/SKILL.md"
  assert_file "$path"
  if [[ -f "$path" ]]; then
    size=$(wc -c < "$path")
    if (( size < 1024 )); then
      echo "FAIL: skill $skill tem apenas $size bytes (esperado > 1KB)"
      FAILED=$((FAILED + 1))
    fi
  fi
done

# v0.3.0: agente gsd-orchestrator + hooks
assert_file ".claude/agents/meta-orchestration/gsd-orchestrator.md"
assert_file ".claude/hooks/README.md"
for hook in gsd-statusline.js gsd-context-monitor.js gsd-prompt-guard.js gsd-read-guard.js gsd-workflow-guard.js gsd-check-update.js gsd-phase-boundary.sh gsd-session-state.sh gsd-validate-commit.sh; do
  assert_file ".claude/hooks/$hook"
done

# ui-ux-pro-max tem data e scripts
assert_dir ".claude/skills/ui-ux-pro-max/data"
assert_dir ".claude/skills/ui-ux-pro-max/scripts"
assert_file ".claude/skills/ui-ux-pro-max/data/ux-guidelines.csv"

# Artefatos de tooling
for art in \
  tooling/ci/quality.yml.template \
  tooling/ci/bundlesize.config.json \
  tooling/ci/lighthouserc.json \
  tooling/ci/pa11yci.json \
  tooling/pre-commit/.pre-commit-config.yaml \
  tooling/jest/jest.setup.a11y.js
do
  assert_file "$art"
done

# v0.2.1: Sprint infrastructure
assert_file ".claude/get-shit-done/references/sprint-slicing.md"
assert_file ".claude/get-shit-done/references/visual-fidelity.md"
assert_file ".claude/get-shit-done/templates/SPRINT.md"
assert_file ".claude/get-shit-done/workflows/gsd-sprint-plan.md"
assert_file ".planning/SPRINTS.md"

# v0.2.2: Orchestrator + docs multi-formato
assert_file ".claude/get-shit-done/references/agent-orchestration.md"
assert_file ".claude/get-shit-done/references/docs-organization.md"
assert_file ".claude/get-shit-done/workflows/gsd-docs-index.md"
assert_file ".claude/get-shit-done/templates/INDEX-subpasta.md"
assert_file "docs/INDEX.md"
assert_file "docs/identidade-visual/INDEX.md"
assert_file "docs/identidade-visual/wireframes/INDEX.md"
assert_file "docs/identidade-visual/mockups/INDEX.md"
assert_file "bin/convert-docs.sh"

# config.json tem slicing_strategy + orchestrator + docs
if [[ -f ".planning/config.json" ]]; then
  if ! python3 -c "
import json
c = json.load(open('.planning/config.json'))
assert 'slicing_strategy' in c, 'slicing_strategy ausente'
assert c['slicing_strategy'] in ('vertical_value', 'admin_first'), 'slicing_strategy inválido'
assert 'visual_tokens_mode' in c, 'visual_tokens_mode ausente'
assert 'sprint_planning' in c, 'sprint_planning ausente'
assert 'orchestrator' in c, 'orchestrator ausente'
assert 'available_agents' in c['orchestrator'], 'orchestrator.available_agents ausente'
assert 'fallback_mode' in c['orchestrator'], 'orchestrator.fallback_mode ausente'
assert 'docs' in c, 'docs ausente'
" 2>/dev/null; then
    echo "FAIL: .planning/config.json sem seções esperadas v0.2.2"
    FAILED=$((FAILED + 1))
  fi
fi

# v0.4.0: commands + agentes completos + workflows/references/templates expandidos
# Commands top-level
for cmd in component deploy endpoint migrate optimize review security test; do
  assert_file ".claude/commands/$cmd.md"
done

# Commands GSD (amostra crítica)
for gcmd in plan-phase execute-phase ui-phase new-project new-milestone autonomous; do
  assert_file ".claude/commands/gsd/$gcmd.md"
done

# Agentes (amostra crítica dos 36)
for agent in gsd-planner gsd-plan-checker gsd-executor gsd-integration-checker gsd-ui-checker gsd-verifier gsd-phase-researcher; do
  assert_file ".claude/agents/$agent.md"
done

# Workflows massivos (amostra dos 76)
for wf in new-project milestone-summary execute-phase ui-phase ship autonomous; do
  assert_file ".claude/get-shit-done/workflows/$wf.md"
done

# References críticos (amostra dos 46)
for ref in context-budget gate-prompts planner-antipatterns thinking-partner tdd; do
  assert_file ".claude/get-shit-done/references/$ref.md"
done

# Templates críticos
for tpl in project milestone roadmap requirements retrospective; do
  assert_file ".claude/get-shit-done/templates/$tpl.md"
done

# Bin gsd-tools.cjs + lib
assert_file ".claude/get-shit-done/bin/gsd-tools.cjs"
assert_dir ".claude/get-shit-done/bin/lib"

if [[ $FAILED -eq 0 ]]; then
  echo "OK — estrutura íntegra"
  exit 0
else
  echo "FAIL: $FAILED checks falharam"
  exit 1
fi
