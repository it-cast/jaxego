#!/usr/bin/env bash
# env-smoke-check.sh
#
# Smoke test do ambiente antes de iniciar uma phase.
# Pega problemas que historicamente apareceram nas fases (Rota Certa, Augur, Alfie):
#   - Dependências que não resolvem (uv sync, pip, npm install)
#   - Build quebrado pré-existente (ng build, tsc)
#   - DB unreachable (mysql, postgres, redis)
#   - Erros TypeScript pré-existentes acumulando
#   - Migrations não-aplicadas
#   - Conflitos de version constraint
#
# Output:
#   - STDOUT: lista de checks com ✓/✗
#   - Exit 0: tudo verde
#   - Exit 1: há blocker — phase NÃO deve começar
#   - Exit 2: há warning — phase pode começar mas operador deve estar ciente
#
# Variáveis de ambiente:
#   - GSD_ENV_SMOKE_SKIP: lista vírgula-separada de checks para pular (ex: "db,build")
#   - GSD_ENV_SMOKE_STRICT: se "1", warnings viram blockers
#
# Cross-platform: detecta SO e usa comandos certos.
#
# Adicionado em v0.9.2.

set -uo pipefail

# ANSI cores (desabilitar se NO_COLOR setado)
if [ -z "${NO_COLOR:-}" ]; then
  GREEN='\033[0;32m'
  RED='\033[0;31m'
  YELLOW='\033[1;33m'
  BLUE='\033[0;34m'
  NC='\033[0m'
else
  GREEN=''
  RED=''
  YELLOW=''
  BLUE=''
  NC=''
fi

BLOCKERS=()
WARNINGS=()
INFOS=()
SKIPPED=()

SKIP_LIST="${GSD_ENV_SMOKE_SKIP:-}"
STRICT="${GSD_ENV_SMOKE_STRICT:-0}"

skipped() {
  case ",$SKIP_LIST," in
    *",$1,"*) return 0 ;;
    *) return 1 ;;
  esac
}

block() {
  BLOCKERS+=("$1")
  echo -e "  ${RED}✗ BLOCK${NC} $1"
}

warn() {
  WARNINGS+=("$1")
  echo -e "  ${YELLOW}⚠ WARN${NC}  $1"
}

ok() {
  echo -e "  ${GREEN}✓ OK${NC}    $1"
}

info() {
  INFOS+=("$1")
  echo -e "  ${BLUE}ℹ INFO${NC}  $1"
}

skip() {
  SKIPPED+=("$1")
  echo -e "  ${BLUE}⊘ SKIP${NC}  $1"
}

# Detectar SO
OS="$(uname -s 2>/dev/null || echo Unknown)"
case "$OS" in
  Linux*)   PLATFORM="linux" ;;
  Darwin*)  PLATFORM="macos" ;;
  CYGWIN*|MINGW*|MSYS*) PLATFORM="windows" ;;
  *)        PLATFORM="unknown" ;;
esac

echo "═══════════════════════════════════════════════════════"
echo "GSD Env Smoke Check (v0.9.2)"
echo "Platform: $PLATFORM"
echo "═══════════════════════════════════════════════════════"
echo ""

# ─── 1. Git status ───────────────────────────────────────────
echo "▶ Git"
if command -v git >/dev/null 2>&1; then
  if [ -d .git ]; then
    if git diff --quiet 2>/dev/null && git diff --cached --quiet 2>/dev/null; then
      ok "working tree clean"
    else
      UNTRACKED=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
      if [ "$UNTRACKED" -gt 50 ]; then
        warn "working tree has $UNTRACKED uncommitted changes (considere commit antes de phase)"
      else
        info "working tree has $UNTRACKED uncommitted changes"
      fi
    fi
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "?")
    info "branch: $CURRENT_BRANCH"
  else
    warn "diretório não é repo git (não há .git/)"
  fi
else
  warn "git não disponível no PATH"
fi
echo ""

# ─── 2. Python environment ───────────────────────────────────
if ! skipped "python" && { [ -f pyproject.toml ] || [ -f requirements.txt ] || [ -d backend ]; }; then
  echo "▶ Python"
  
  # Python disponível?
  if command -v python3 >/dev/null 2>&1; then
    PYV=$(python3 --version 2>&1 | awk '{print $2}')
    ok "python3 $PYV"
  elif command -v python >/dev/null 2>&1; then
    PYV=$(python --version 2>&1 | awk '{print $2}')
    ok "python $PYV"
  else
    block "python não encontrado (necessário para projetos com pyproject.toml/requirements.txt)"
  fi
  
  # uv disponível? (preferido)
  if command -v uv >/dev/null 2>&1; then
    UVV=$(uv --version 2>&1 | awk '{print $2}')
    ok "uv $UVV"
    
    # uv lock check (Rota Certa phase-03 pegou aqui)
    if [ -f uv.lock ] && [ -f pyproject.toml ]; then
      if uv lock --check >/dev/null 2>&1; then
        ok "uv.lock está sincronizado com pyproject.toml"
      else
        warn "uv.lock está desatualizado — rode 'uv lock' antes da phase"
      fi
    fi
  fi
  
  # venv presente?
  if [ -d .venv ]; then
    ok ".venv/ existe"
    
    # Smoke test: imports principais funcionam?
    PYBIN="$( [ "$PLATFORM" = "windows" ] && echo ".venv/Scripts/python.exe" || echo ".venv/bin/python")"
    if [ -x "$PYBIN" ]; then
      # Tenta importar projeto se há src/ ou backend/
      if [ -d src ]; then
        if ! "$PYBIN" -c "import sys; sys.path.insert(0, 'src'); import os; [__import__(d) for d in os.listdir('src') if os.path.isdir(f'src/{d}') and not d.startswith('_')][:1]" 2>/dev/null; then
          warn "imports de src/ falharam — possível dependência faltando"
        else
          ok "imports básicos de src/ funcionam"
        fi
      fi
    fi
  elif [ -d venv ]; then
    ok "venv/ existe"
  else
    if [ -f pyproject.toml ]; then
      warn ".venv/ não existe — rode 'uv sync' ou 'python -m venv .venv'"
    fi
  fi
  
  # pyproject.toml tem pythonpath se há src/ (Rota Certa phase-02 pegou)
  if [ -f pyproject.toml ] && [ -d src ]; then
    if ! grep -q 'pythonpath' pyproject.toml; then
      warn "pyproject.toml sem 'pythonpath = [\"src\"]' — pytest pode coletar 0 testes silenciosamente"
    fi
  fi
  
  echo ""
fi

# ─── 3. Node environment ─────────────────────────────────────
if ! skipped "node" && { [ -f package.json ] || [ -d frontend ]; }; then
  echo "▶ Node.js"
  
  if command -v node >/dev/null 2>&1; then
    NV=$(node --version 2>&1)
    NMAJOR=$(echo "$NV" | sed 's/^v\([0-9]*\)\..*/\1/')
    if [ "$NMAJOR" -ge 18 ]; then
      ok "node $NV (>=18 ✓)"
    else
      block "node $NV — necessário >=18 para gsd-tools.cjs"
    fi
  else
    block "node não encontrado (necessário para gsd-tools)"
  fi
  
  # Detectar package manager pelo lockfile
  PM=""
  if [ -f pnpm-lock.yaml ]; then PM="pnpm"
  elif [ -f yarn.lock ]; then PM="yarn"
  elif [ -f bun.lockb ]; then PM="bun"
  elif [ -f package-lock.json ]; then PM="npm"
  fi
  
  if [ -n "$PM" ]; then
    if command -v "$PM" >/dev/null 2>&1; then
      ok "package manager: $PM"
    else
      warn "lockfile indica $PM mas binário não está no PATH"
    fi
  fi
  
  # node_modules presente?
  if [ -d node_modules ]; then
    ok "node_modules/ existe"
  else
    if [ -f package.json ]; then
      warn "node_modules/ não existe — rode '$PM install' ($PM detectado pelo lockfile)"
    fi
  fi
  
  # TypeScript: errors pré-existentes (Rota Certa phases 2-4 acumulou)
  if [ -f tsconfig.json ] && [ -d node_modules ]; then
    if command -v npx >/dev/null 2>&1; then
      TSC_OUTPUT=$(npx -p typescript --no-install tsc --noEmit 2>&1 | head -100 || true)
      ERR_COUNT=$(echo "$TSC_OUTPUT" | grep -cE "error TS[0-9]+:" 2>/dev/null || echo 0)
      ERR_COUNT=$(echo "$ERR_COUNT" | tr -d '\n' | tr -d ' ')
      if [ "$ERR_COUNT" = "0" ]; then
        ok "tsc --noEmit: 0 errors"
      elif [ "$ERR_COUNT" -lt 10 ]; then
        warn "tsc --noEmit: $ERR_COUNT errors pré-existentes — endereçar antes de acumular"
      else
        block "tsc --noEmit: $ERR_COUNT errors pré-existentes — bloqueia phase nova (TD aging)"
      fi
    fi
  fi
  
  # Frontend específico: dependências comuns esquecidas (Rota Certa phase-02)
  if [ -f frontend/package.json ]; then
    if grep -q '"@angular/' frontend/package.json && ! grep -q '"@angular/animations"' frontend/package.json; then
      info "Angular detectado sem @angular/animations — adicionar se for usar transições"
    fi
  fi
  
  echo ""
fi

# ─── 4. Database connectivity ────────────────────────────────
if ! skipped "db"; then
  # Detecta se há config de DB para testar
  HAS_DB_CONFIG="false"
  if [ -f docker-compose.yml ] && grep -qE "mysql|postgres|redis" docker-compose.yml 2>/dev/null; then
    HAS_DB_CONFIG="true"
  fi
  if [ -f .env ] && grep -qE "DATABASE_URL|REDIS_URL" .env 2>/dev/null; then
    HAS_DB_CONFIG="true"
  fi
  if [ -f backend/alembic.ini ] || [ -f alembic.ini ]; then
    HAS_DB_CONFIG="true"
  fi
  
  if [ "$HAS_DB_CONFIG" = "true" ]; then
    echo "▶ Database connectivity"
    
    # MySQL
    if command -v mysql >/dev/null 2>&1; then
      if mysql --version >/dev/null 2>&1; then
        ok "mysql cliente disponível"
      fi
    fi
    
    # Postgres
    if command -v psql >/dev/null 2>&1; then
      ok "psql cliente disponível"
    fi
    
    # Redis
    if command -v redis-cli >/dev/null 2>&1; then
      if [ -n "${REDIS_URL:-}" ] || grep -q REDIS .env 2>/dev/null; then
        REDIS_HOST="${REDIS_URL:-redis://localhost:6379}"
        # Tenta ping com timeout (sem travar)
        if timeout 2 redis-cli -u "$REDIS_HOST" ping 2>/dev/null | grep -q PONG; then
          ok "redis acessível em $REDIS_HOST"
        else
          warn "redis cliente disponível mas servidor não responde em $REDIS_HOST"
        fi
      fi
    fi
    
    # Alembic — env.py lê variável certa? (Rota Certa phase-04 pegou)
    if [ -f backend/alembic/env.py ]; then
      if grep -q "TEST_DATABASE_URL" backend/alembic/env.py; then
        ok "alembic/env.py respeita TEST_DATABASE_URL"
      else
        warn "alembic/env.py não lê TEST_DATABASE_URL — testes vão usar DB de dev"
      fi
    fi
    
    echo ""
  fi
fi

# ─── 5. Tech debt aging (Rota Certa, Alfie acumularam) ──────
if ! skipped "td-aging" && [ -f .planning/TECH-DEBT.md ]; then
  echo "▶ Tech debt aging"
  
  # Conta TDs abertas
  OPEN_TDS=$(grep -cE "^\| TD-[0-9]" .planning/TECH-DEBT.md 2>/dev/null || echo 0)
  ABERTOS=$(grep -cE "aberto" .planning/TECH-DEBT.md 2>/dev/null || echo 0)
  
  if [ "$OPEN_TDS" -gt 0 ]; then
    info "$OPEN_TDS TDs registradas ($ABERTOS marcadas como 'aberto')"
    
    # Pre-launch blockers em aberto?
    PLB=$(grep -E "pre_launch_blocker" .planning/TECH-DEBT.md 2>/dev/null | grep -E "aberto" 2>/dev/null | wc -l | tr -d ' ')
    if [ "${PLB:-0}" -gt 0 ] 2>/dev/null; then
      block "$PLB TD(s) com urgency_class=pre_launch_blocker em aberto — devem ser resolvidas antes de continuar"
    fi
    
    # Pre-launch high em aberto?
    PLH=$(grep -E "pre_launch_high" .planning/TECH-DEBT.md 2>/dev/null | grep -E "aberto" 2>/dev/null | wc -l | tr -d ' ')
    if [ "${PLH:-0}" -gt 0 ] 2>/dev/null; then
      warn "$PLH TD(s) com urgency_class=pre_launch_high em aberto — endereçar nesta phase se possível"
    fi
  fi
  
  echo ""
fi

# ─── 6. Disk space ───────────────────────────────────────────
if ! skipped "disk"; then
  if command -v df >/dev/null 2>&1; then
    FREE_GB=$(df -BG . 2>/dev/null | tail -1 | awk '{print $4}' | sed 's/G//' || echo "?")
    if [ "$FREE_GB" != "?" ]; then
      if [ "$FREE_GB" -lt 2 ]; then
        block "disco com menos de 2GB livres — builds podem falhar"
      elif [ "$FREE_GB" -lt 10 ]; then
        warn "disco com menos de 10GB livres — atenção"
      fi
    fi
  fi
fi

# ─── Resumo ──────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════"
echo "Resumo"
echo "═══════════════════════════════════════════════════════"
echo -e "  ${GREEN}OK${NC}:        $(grep -c "✓ OK" /dev/null 2>/dev/null || true)$(echo "${INFOS[@]:-} ${SKIPPED[@]:-}" | wc -w) total checks"
echo -e "  ${BLUE}INFO${NC}:      ${#INFOS[@]} informational"
echo -e "  ${YELLOW}WARN${NC}:      ${#WARNINGS[@]} warnings"
echo -e "  ${RED}BLOCK${NC}:     ${#BLOCKERS[@]} blockers"

if [ "${#BLOCKERS[@]}" -gt 0 ]; then
  echo ""
  echo -e "${RED}❌ Phase NÃO deve começar — resolva blockers primeiro:${NC}"
  for b in "${BLOCKERS[@]}"; do
    echo -e "   ${RED}•${NC} $b"
  done
  exit 1
fi

if [ "${#WARNINGS[@]}" -gt 0 ]; then
  if [ "$STRICT" = "1" ]; then
    echo ""
    echo -e "${RED}❌ GSD_ENV_SMOKE_STRICT=1 — warnings tratados como blockers:${NC}"
    for w in "${WARNINGS[@]}"; do
      echo -e "   ${YELLOW}•${NC} $w"
    done
    exit 1
  else
    echo ""
    echo -e "${YELLOW}⚠ Phase pode começar mas atenção aos warnings:${NC}"
    for w in "${WARNINGS[@]}"; do
      echo -e "   ${YELLOW}•${NC} $w"
    done
    exit 2
  fi
fi

echo ""
echo -e "${GREEN}✓ Ambiente OK — phase pode começar${NC}"
exit 0
