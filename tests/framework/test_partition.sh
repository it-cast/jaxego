#!/usr/bin/env bash
# tests/framework/test_partition.sh
# Particionamento determinístico de waves (v0.9.6).
# Prova que a lógica de fronteira de arquivos — antes prosa no agente
# gsd-wave-dispatcher — agora é código com comportamento verificável.
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

part() { node "$GSD_TOOLS" partition "$TMPDIR_T/$1.json"; }
field() { part "$1" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const r=JSON.parse(d);console.log(JSON.stringify(eval('r.'+process.argv[1])))})" "$2"; }

echo "[partition] back/front disjuntos paralelizam"
cat > "$TMPDIR_T/bf.json" << 'EOF'
{"tasks":[{"id":"B","files":["app/api/x.py"]},{"id":"F","files":["web/src/x.ts"]}]}
EOF
check "2 grupos" "[ \"\$(field bf 'groups.length')\" = '2' ]"
check "parallel_viable=true" "[ \"\$(field bf 'parallel_viable')\" = 'true' ]"

echo "[partition] arquivo compartilhado serializa entre si (mesmo grupo)"
cat > "$TMPDIR_T/shared.json" << 'EOF'
{"tasks":[{"id":"A","files":["app/svc.py","app/a.py"]},{"id":"B","files":["app/svc.py","app/b.py"]}]}
EOF
check "1 grupo único" "[ \"\$(field shared 'groups.length')\" = '1' ]"
check "grupo contém A e B" "part shared | grep -q '\"A\"' && part shared | grep -q '\"B\"'"

echo "[partition] migration vai para trilho serial"
cat > "$TMPDIR_T/mig.json" << 'EOF'
{"tasks":[{"id":"M","files":["alembic/versions/001_x.py"]},{"id":"F","files":["web/x.ts"]}]}
EOF
check "M no serial" "[ \"\$(field mig 'serial[0]')\" = '\"M\"' ]"

echo "[partition] pyproject.toml arrasta lockfile → serial"
cat > "$TMPDIR_T/dep.json" << 'EOF'
{"tasks":[{"id":"D","files":["pyproject.toml"]}]}
EOF
check "D no serial por lockfile implícito" "part dep | grep -q 'uv.lock'"

echo "[partition] package.json arrasta lockfiles JS → serial"
cat > "$TMPDIR_T/depjs.json" << 'EOF'
{"tasks":[{"id":"D","files":["web/package.json"]}]}
EOF
check "lockfile JS detectado" "part depjs | grep -qE 'package-lock|yarn.lock|pnpm-lock'"

echo "[partition] models/* arrastam __init__.py (registro central implícito)"
cat > "$TMPDIR_T/models.json" << 'EOF'
{"tasks":[{"id":"M1","files":["app/models/a.py"]},{"id":"M2","files":["app/models/b.py"]}]}
EOF
check "M1 e M2 no MESMO grupo (não paralelizam)" "[ \"\$(field models 'groups.length')\" = '1' ]"
check "razão cita __init__.py" "part models | grep -q '__init__.py'"

echo "[partition] task sem files declarados → serial (conservador)"
cat > "$TMPDIR_T/vague.json" << 'EOF'
{"tasks":[{"id":"VAGUE"},{"id":"F","files":["web/x.ts"]}]}
EOF
check "VAGUE no serial" "part vague | grep -B1 -A3 '\"serial\"' | grep -q 'VAGUE'"
check "razão explica conservadorismo" "part vague | grep -q 'conservador'"

echo "[partition] wave toda conflitante declara serial honestamente"
cat > "$TMPDIR_T/conflict.json" << 'EOF'
{"tasks":[{"id":"A","files":["app/x.py"]},{"id":"B","files":["app/x.py"]}]}
EOF
check "parallel_viable=false" "[ \"\$(field conflict 'parallel_viable')\" = 'false' ]"
check "summary declara 'wave é serial'" "part conflict | grep -q 'wave é serial'"

echo "[partition] paths Windows normalizados (cross-platform)"
cat > "$TMPDIR_T/winpath.json" << 'EOF'
{"tasks":[{"id":"A","files":["app\\models\\a.py"]},{"id":"B","files":["app/models/b.py"]}]}
EOF
check "backslash e slash colidem no mesmo __init__" "[ \"\$(field winpath 'groups.length')\" = '1' ]"

echo "[partition] cenário realista misto (5 classes de task numa wave)"
cat > "$TMPDIR_T/mixed.json" << 'EOF'
{"tasks":[
 {"id":"BACK-1","files":["app/api/forecasts.py","app/services/sim.py"]},
 {"id":"FRONT-1","files":["web/src/app/forecasts/list.component.ts"]},
 {"id":"MIG-1","files":["alembic/versions/0042_add_brier.py"]},
 {"id":"BACK-2","files":["app/services/sim.py","app/schemas/sim.py"]},
 {"id":"DEP-1","files":["pyproject.toml"]}
]}
EOF
check "MIG-1 e DEP-1 no serial (2)" "[ \"\$(field mixed 'serial.length')\" = '2' ]"
check "BACK-1+BACK-2 agrupados, FRONT-1 separado (2 grupos)" "[ \"\$(field mixed 'groups.length')\" = '2' ]"
check "reasons explicam cada decisão" "part mixed | grep -q 'compartilha app/services/sim.py'"

echo "[partition] erros de input são claros"
cat > "$TMPDIR_T/bad.json" << 'EOF'
{"tasks": "não é array"}
EOF
check "input inválido falha com mensagem" "! part bad > /dev/null 2>&1"

echo "[partition] integração — agente wave-dispatcher chama o comando"
check "agente referencia gsd-tools partition" "grep -q 'partition' '$ROOT/.claude/agents/gsd-wave-dispatcher.md'"
check "agente instrui obedecer à saída" "grep -q 'obedece à saída' '$ROOT/.claude/agents/gsd-wave-dispatcher.md'"

exit $FAIL
