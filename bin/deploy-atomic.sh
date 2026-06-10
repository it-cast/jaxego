#!/usr/bin/env bash
# deploy-atomic.sh — TEMPLATE de symlink atomic deploy para monorepo poliglota
#
# Estratégia: symlink atomic (releases versionadas + current symlink + shared/).
# Ver skill: .claude/skills/domain/monorepo-deploy-safety/SKILL.md
#
# ESTE É UM TEMPLATE. Adaptar:
#   - DEPLOY_ROOT, APP_NAME, SERVICE_NAME
#   - comandos de build/migration ao seu stack
#   - health check endpoints
#
# Uso:
#   ./deploy-atomic.sh                    # deploy da branch atual
#   ./deploy-atomic.sh --rollback         # rollback para release anterior
#   ./deploy-atomic.sh --dry-run          # mostra o que faria, não executa
#
# Pré-requisitos no servidor:
#   - estrutura /opt/{app}/{releases,shared,current}
#   - shared/.env com secrets
#   - systemd ou supervisor configurado para o serviço
#
# Adicionado em v0.9.3.

set -euo pipefail

# ─── Configuração (ADAPTAR) ──────────────────────────────────
APP_NAME="${APP_NAME:-meuapp}"
DEPLOY_ROOT="${DEPLOY_ROOT:-/opt/$APP_NAME}"
SERVICE_NAME="${SERVICE_NAME:-$APP_NAME-api}"
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"
FRONTEND_HEALTH_URL="${FRONTEND_HEALTH_URL:-http://localhost/}"
KEEP_RELEASES="${KEEP_RELEASES:-5}"
RELOAD_CMD="${RELOAD_CMD:-systemctl reload $SERVICE_NAME}"

RELEASES_DIR="$DEPLOY_ROOT/releases"
SHARED_DIR="$DEPLOY_ROOT/shared"
CURRENT_LINK="$DEPLOY_ROOT/current"
LOCK_FILE="$DEPLOY_ROOT/deploy.lock"

# ─── Cores ───────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

log()  { echo -e "${BLUE}▶${NC} $*"; }
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }

DRY_RUN=false
ROLLBACK=false

for arg in "$@"; do
  case "$arg" in
    --dry-run)  DRY_RUN=true ;;
    --rollback) ROLLBACK=true ;;
  esac
done

run() {
  if [ "$DRY_RUN" = true ]; then
    echo "    [dry-run] $*"
  else
    eval "$@"
  fi
}

# ─── Lock (previne deploy concorrente) ───────────────────────
acquire_lock() {
  if [ -f "$LOCK_FILE" ]; then
    local pid
    pid=$(cat "$LOCK_FILE" 2>/dev/null || echo "?")
    err "Deploy já em andamento (lock: $LOCK_FILE, pid: $pid)"
    err "Se for lock órfão, remova: rm $LOCK_FILE"
    exit 1
  fi
  if [ "$DRY_RUN" = false ]; then
    echo $$ > "$LOCK_FILE"
    trap 'rm -f "$LOCK_FILE"' EXIT
  fi
}

# ─── Rollback ────────────────────────────────────────────────
do_rollback() {
  log "ROLLBACK — voltando para release anterior"
  
  # Achar release atual e anterior
  local current_release prev_release
  current_release=$(readlink "$CURRENT_LINK" 2>/dev/null | xargs basename 2>/dev/null || echo "")
  prev_release=$(ls -1t "$RELEASES_DIR" 2>/dev/null | grep -v "^$current_release$" | head -1 || echo "")
  
  if [ -z "$prev_release" ]; then
    err "Não há release anterior para rollback"
    exit 1
  fi
  
  log "Atual: $current_release → Anterior: $prev_release"
  
  # Trocar symlink atomicamente
  run "ln -sfn '$RELEASES_DIR/$prev_release' '$CURRENT_LINK.tmp'"
  run "mv -T '$CURRENT_LINK.tmp' '$CURRENT_LINK'"
  ok "Symlink revertido"
  
  # Reload
  run "$RELOAD_CMD"
  ok "Serviço recarregado"
  
  # Health check
  sleep 2
  if [ "$DRY_RUN" = false ] && command -v curl >/dev/null 2>&1; then
    if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
      ok "Health check OK após rollback"
    else
      err "Health check FALHOU após rollback — investigar manualmente"
      exit 1
    fi
  fi
  
  warn "ATENÇÃO: se a release com problema rodou migrations, pode ser necessário 'alembic downgrade' manual"
  ok "Rollback concluído"
  exit 0
}

# ─── Deploy ──────────────────────────────────────────────────
do_deploy() {
  local timestamp release_dir prev_release
  timestamp=$(date +%Y-%m-%d-%H%M%S)
  release_dir="$RELEASES_DIR/$timestamp"
  prev_release=$(readlink "$CURRENT_LINK" 2>/dev/null | xargs basename 2>/dev/null || echo "")
  
  log "Deploy $APP_NAME — release $timestamp"
  echo ""

  # ── Passo 1: Pre-flight check ──
  log "1. Pre-flight check"
  
  if [ -f bin/env-smoke-check.sh ]; then
    if [ "$DRY_RUN" = false ]; then
      bash bin/env-smoke-check.sh || { err "env-smoke-check falhou — abortando"; exit 1; }
    else
      echo "    [dry-run] bash bin/env-smoke-check.sh"
    fi
  fi
  
  if [ ! -f "$SHARED_DIR/.env" ]; then
    if [ "$DRY_RUN" = true ]; then
      warn "[dry-run] shared/.env não existe (em deploy real isto abortaria)"
    else
      err "shared/.env não existe em $SHARED_DIR — secrets ausentes"
      exit 1
    fi
  fi
  ok "Pre-flight OK"

  # ── Passo 2: Subir nova release ──
  log "2. Criando release $timestamp"
  run "mkdir -p '$release_dir'"
  
  # Backend (sem .env, __pycache__, .venv)
  run "rsync -a --exclude='.env' --exclude='__pycache__' --exclude='.venv' --exclude='*.pyc' backend/ '$release_dir/backend/'"
  
  # Frontend (build já feito no CI, copiar dist)
  if [ -d frontend/dist ]; then
    run "cp -r frontend/dist '$release_dir/frontend-dist'"
  elif [ -d frontend/www ]; then
    run "cp -r frontend/www '$release_dir/frontend-dist'"
  else
    warn "frontend/dist ou frontend/www não encontrado — pulando frontend"
  fi
  
  # Symlinks para shared (config, logs, uploads)
  run "ln -sfn '$SHARED_DIR/.env' '$release_dir/backend/.env'"
  run "ln -sfn '$SHARED_DIR/logs' '$release_dir/backend/logs'"
  run "ln -sfn '$SHARED_DIR/uploads' '$release_dir/backend/uploads'"
  
  # RELEASE-INFO.json
  local git_sha
  git_sha=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
  if [ "$DRY_RUN" = false ]; then
    cat > "$release_dir/RELEASE-INFO.json" << INFOEOF
{
  "release": "$timestamp",
  "git_sha": "$git_sha",
  "deployed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "deployed_by": "${USER:-unknown}",
  "previous_release": "$prev_release"
}
INFOEOF
  fi
  ok "Release criada em $release_dir"

  # ── Passo 3: Migrations ANTES do switch ──
  log "3. Migrations (antes do switch — forward-compatible)"
  if [ -f "$release_dir/backend/alembic.ini" ]; then
    if [ "$DRY_RUN" = false ]; then
      ( cd "$release_dir/backend" && alembic upgrade head ) || {
        err "Migrations FALHARAM — abortando deploy, release antiga continua servindo"
        rm -rf "$release_dir"
        exit 1
      }
    else
      echo "    [dry-run] cd $release_dir/backend && alembic upgrade head"
    fi
    ok "Migrations aplicadas"
  else
    warn "Sem alembic.ini — pulando migrations"
  fi

  # ── Passo 4: Trocar symlink atomicamente ──
  log "4. Trocando symlink (atômico)"
  run "ln -sfn '$release_dir' '$CURRENT_LINK.tmp'"
  run "mv -T '$CURRENT_LINK.tmp' '$CURRENT_LINK'"
  ok "current → $timestamp"

  # ── Passo 5: Graceful reload ──
  log "5. Graceful reload do backend"
  run "$RELOAD_CMD"
  ok "Backend recarregado"

  # ── Passo 6: Frontend (Nginx re-lê symlink) ──
  log "6. Reload Nginx (frontend)"
  if command -v nginx >/dev/null 2>&1; then
    run "nginx -s reload"
    ok "Nginx recarregado"
  else
    warn "nginx não encontrado — pular se frontend não usa Nginx"
  fi

  # ── Passo 7: Health check ──
  log "7. Health check pós-deploy"
  if [ "$DRY_RUN" = false ] && command -v curl >/dev/null 2>&1; then
    sleep 3
    local health_ok=true
    
    if ! curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
      err "Backend health check FALHOU ($HEALTH_URL)"
      health_ok=false
    else
      ok "Backend health OK"
    fi
    
    if ! curl -sf "$FRONTEND_HEALTH_URL" >/dev/null 2>&1; then
      warn "Frontend health check falhou ($FRONTEND_HEALTH_URL)"
    else
      ok "Frontend health OK"
    fi
    
    # ── Passo 8: Rollback automático se health falhou ──
    if [ "$health_ok" = false ]; then
      err "Health check falhou — ROLLBACK AUTOMÁTICO"
      if [ -n "$prev_release" ]; then
        ln -sfn "$RELEASES_DIR/$prev_release" "$CURRENT_LINK.tmp"
        mv -T "$CURRENT_LINK.tmp" "$CURRENT_LINK"
        eval "$RELOAD_CMD"
        err "Revertido para $prev_release. Investigar a release $timestamp."
        warn "Se migrations rodaram, considere 'alembic downgrade' manual"
      else
        err "Sem release anterior para rollback — intervenção manual necessária"
      fi
      exit 1
    fi
  else
    warn "curl indisponível ou dry-run — health check pulado"
  fi

  # ── Passo 9: Cleanup ──
  log "9. Cleanup (mantendo últimas $KEEP_RELEASES releases)"
  if [ "$DRY_RUN" = false ]; then
    local to_delete
    to_delete=$(ls -1t "$RELEASES_DIR" 2>/dev/null | tail -n +$((KEEP_RELEASES + 1)) || true)
    for old in $to_delete; do
      rm -rf "$RELEASES_DIR/$old"
      echo "    removido: $old"
    done
  fi
  ok "Cleanup concluído"

  echo ""
  ok "Deploy $timestamp concluído com sucesso"
  echo "   git_sha: $git_sha"
  echo "   anterior: $prev_release"
  echo "   rollback: ./deploy-atomic.sh --rollback"
}

# ─── Main ────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════"
echo "GSD Atomic Deploy — $APP_NAME"
[ "$DRY_RUN" = true ] && echo "(DRY RUN — nada será executado)"
echo "═══════════════════════════════════════════════════════"
echo ""

acquire_lock

if [ "$ROLLBACK" = true ]; then
  do_rollback
else
  do_deploy
fi
