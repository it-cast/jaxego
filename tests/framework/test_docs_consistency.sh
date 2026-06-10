#!/usr/bin/env bash
# tests/framework/test_docs_consistency.sh
# Consistência docs ↔ código (v0.9.6).
#
# MOTIVAÇÃO: a revisão da v0.9.5 encontrou 3 contradições internas em 20 min
# de grep — changelog dizendo "159 arquivos ainda têm paths" depois de corrigir
# todos, go.md falando em "7 gates" num framework de 8, e docs instruindo
# `gsd-tools.cjs --help` que retornava erro. Um framework cuja tese é
# reconciliação de estado não pode ter o próprio estado documental divergindo.
# Este teste torna essa classe de bug detectável por máquina.
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

# Docs "atuais" — afirmam o estado presente do framework.
# (FRAMEWORK-STATUS.md e MIGRACAO-*.md são changelogs: entradas históricas podem
#  citar números antigos, desde que claims superados carreguem marcador RESOLVIDO.)
CURRENT_DOCS="README.md CLAUDE.md INSTALLATION.md GUIA-PROJETO-NOVO.md GUIA-PROJETO-LEGADO.md PERMISSIONS.md .claude/commands/gsd/go.md .claude/get-shit-done/references/gates-v3.md"

echo "[docs↔código] Contagens reais no disco"
SKILLS_REAL=$(find .claude/skills -name SKILL.md | wc -l | tr -d ' ')
AGENTS_REAL=$(find .claude/agents -name '*.md' | wc -l | tr -d ' ')
COMMANDS_REAL=$(find .claude/commands -name '*.md' | wc -l | tr -d ' ')
echo "  (skills=$SKILLS_REAL agentes=$AGENTS_REAL commands=$COMMANDS_REAL)"

echo "[docs↔código] CLAUDE.md declara as contagens corretas"
check "skills ($SKILLS_REAL) batem" "grep -q \"$SKILLS_REAL skills\" CLAUDE.md"
check "agentes ($AGENTS_REAL) batem" "grep -q \"$AGENTS_REAL agentes\" CLAUDE.md"
check "commands ($COMMANDS_REAL) batem" "grep -q \"$COMMANDS_REAL slash commands\" CLAUDE.md"

echo "[docs↔código] Número de gates consistente (8) em docs atuais"
GATE_COUNT_REAL=8
for doc in $CURRENT_DOCS; do
  [ -f "$doc" ] || continue
  check "$doc não afirma '7 gates' como estado atual" "! grep -qE '(tem|são|os|aplica) 7 gates' '$doc'"
done
check "gates-v3.md documenta Gate 8" "grep -q 'Gate 8' .claude/get-shit-done/references/gates-v3.md"
check "go.md fala em 8 gates" "grep -q '8 gates' .claude/commands/gsd/go.md"

echo "[docs↔código] Claims superados em changelogs carregam marcador RESOLVIDO"
# Qualquer linha que afirme paths Windows pendentes deve estar riscada/anotada
if grep -n "159 outros arquivos" FRAMEWORK-STATUS.md > /dev/null 2>&1; then
  check "claims de '159 arquivos pendentes' anotados como RESOLVIDO" \
    "! grep '159 outros arquivos' FRAMEWORK-STATUS.md | grep -qv 'RESOLVIDO'"
fi

echo "[docs↔código] Zero paths Windows em código/config do framework"
check "nenhum C:/ em .claude/" "! grep -rq 'C:/' .claude/"
check "nenhum C:/ em bin/" "! grep -rq 'C:/' bin/"

echo "[docs↔código] Toda invocação de gsd-tools documentada é executável"
check "filename correto (gsd-tools, não gsd:tools) em todos os .md" \
  "! grep -rq 'gsd:tools.cjs' --include='*.md' --exclude='FRAMEWORK-STATUS.md' --exclude='MIGRACAO-*.md' ."
check "gsd-tools --help retorna usage com exit 0" \
  "node .claude/get-shit-done/bin/gsd-tools.cjs --help > /dev/null 2>&1"
check "gsd-tools sem args retorna usage" \
  "node .claude/get-shit-done/bin/gsd-tools.cjs 2>&1 | grep -q 'Usage'"
check "proteção contra --help em comandos mantida" \
  "! node .claude/get-shit-done/bin/gsd-tools.cjs commit --help > /dev/null 2>&1"

echo "[docs↔código] Commands citados nos guias existem como arquivo"
# Extrai todo /gsd:<nome> citado nos docs atuais e verifica que o command existe
MISSING_CMDS=0
for doc in $CURRENT_DOCS README.md; do
  [ -f "$doc" ] || continue
  for cmd in $(grep -ohE '/gsd:[a-z-]+' "$doc" | sort -u | sed 's|/gsd:||'); do
    if [ ! -f ".claude/commands/gsd/${cmd}.md" ]; then
      echo "  ✗ $doc cita /gsd:${cmd} mas .claude/commands/gsd/${cmd}.md não existe"
      MISSING_CMDS=1
    fi
  done
done
check "nenhum command fantasma citado em docs atuais" "[ $MISSING_CMDS -eq 0 ]"

echo "[docs↔código] Fingerprints cobrem todas as skills no disco"
FP_RESULT=$(node -e "
const fs=require('fs');
const src=fs.readFileSync('.claude/hooks/gsd-skill-application-check.js','utf8');
const m=src.match(/const SKILL_FINGERPRINTS = (\{[\s\S]*?\n\});/);
const map=eval('('+m[1]+')');
const {execSync}=require('child_process');
const onDisk=execSync(\"find .claude/skills -name SKILL.md | sed 's|.claude/skills/||;s|/SKILL.md||'\").toString().trim().split('\n');
const semFp=onDisk.filter(s=>!Object.keys(map).includes(s));
const orfaos=Object.keys(map).filter(k=>!onDisk.includes(k));
if(semFp.length||orfaos.length){console.log('FAIL sem_fp='+semFp.join(',')+' orfaos='+orfaos.join(','));process.exit(1)}
console.log('OK '+Object.keys(map).length);
" 2>&1)
check "fingerprints 1:1 com skills ($FP_RESULT)" "echo '$FP_RESULT' | grep -q '^OK'"

echo "[docs↔código] Contagem de suites prometida nos docs bate com run-all.sh"
SUITES_REAL=$(grep -cE '"test_[a-z_0-9]+\.sh"' tests/framework/run-all.sh)
for doc in INSTALLATION.md README.md GUIA-PROJETO-NOVO.md TUTORIAL-COMPLETO.md; do
  [ -f "$doc" ] || continue
  BAD=$(grep -oE '[0-9]+/[0-9]+ suites' "$doc" | grep -v "^$SUITES_REAL/$SUITES_REAL " | grep -v "^$SUITES_REAL/$SUITES_REAL$" || true)
  check "$doc promete $SUITES_REAL/$SUITES_REAL suites (não outro número)" "[ -z \"\$(grep -oE '[0-9]+/[0-9]+ suites' '$doc' | grep -v \"$SUITES_REAL/$SUITES_REAL\")\" ]"
done

exit $FAIL
