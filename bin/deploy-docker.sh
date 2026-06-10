#!/usr/bin/env bash
# deploy-docker.sh — Deploy de monorepo via Docker + GHCR + rollback por tag
#
# Modelo (decidido com o operador, v0.9.4):
#   - Apps em Docker (api, web), imagens no GHCR
#   - MySQL NATIVO na VPS, FORA do Docker (nunca no compose)
#   - Backup pré-migration obrigatório pro B2 antes de qualquer migration
#   - Rollback por tag de imagem (imagens versionadas no registry)
#   - JAMAIS usa docker compose down -v (apagaria volumes)
#
# Princípio central: a IMAGEM é descartável, os DADOS são sagrados.
#   - Deploy troca imagens (descartável)
#   - Banco nativo na VPS nunca é tocado pelo deploy
#   - Migration roda antes do switch, com backup antes
#
# Uso:
#   ./deploy-docker.sh --tag=2026-05-22-1430       # deploy de uma tag específica
#   ./deploy-docker.sh --tag=SHA --rollback-to=SHA_ANTERIOR
#   ./deploy-docker.sh --rollback                  # volta pra tag anterior conhecida
#   ./deploy-docker.sh --dry-run --tag=...
#
# Adicionado em v0.9.4.

set -euo pipefail

# ─── Configuração (ADAPTAR) ──────────────────────────────────
APP_NAME="${APP_NAME:-meuapp}"
DEPLOY_ROOT="${DEPLOY_ROOT:-/opt/$APP_NAME}"
COMPOSE_FILE="${COMPOSE_FILE:-$DEPLOY_ROOT/docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-$DEPLOY_ROOT/shared/.env}"
REGISTRY="${REGISTRY:-ghcr.io}"
REGISTRY_NS="${REGISTRY_NS:-seu-usuario/$APP_NAME}"   # ghcr.io/seu-usuario/meuapp
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"
TAG_STATE_FILE="${TAG_STATE_FILE:-$DEPLOY_ROOT/shared/.deployed-tags.json}"
BACKUP_SCRIPT="${BACKUP_SCRIPT:-$DEPLOY_ROOT/bin/backup-mysql-b2.sh}"
LOCK_FILE="$DEPLOY_ROOT/deploy.lock"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${BLUE}▶${NC} $*"; }
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }

DRY_RUN=false
ROLLBACK=false
TAG=""
ROLLBACK_TO=""

for arg in "$@"; do
  case "$arg" in
    --dry-run)        DRY_RUN=true ;;
    --rollback)       ROLLBACK=true ;;
    --tag=*)          TAG="${arg#*=}" ;;
    --rollback-to=*)  ROLLBACK_TO="${arg#*=}" ;;
  esac
done

run() {
  if [ "$DRY_RUN" = true ]; then echo "    [dry-run] $*"; else eval "$@"; fi
}

acquire_lock() {
  if [ -f "$LOCK_FILE" ]; then
    err "Deploy já em andamento (lock: $LOCK_FILE). Se órfão: rm $LOCK_FILE"
    exit 1
  fi
  if [ "$DRY_RUN" = false ]; then
    echo $$ > "$LOCK_FILE"
    trap 'rm -f "$LOCK_FILE"' EXIT
  fi
}

# Detecta se há migrations pendentes comparando current vs heads
has_pending_migrations() {
  if [ "$DRY_RUN" = true ]; then return 0; fi
  local current heads
  current=$(docker compose -f "$COMPOSE_FILE" run --rm api alembic current 2>/dev/null | tail -1 || echo "")
  heads=$(docker compose -f "$COMPOSE_FILE" run --rm api alembic heads 2>/dev/null | tail -1 || echo "")
  [ "$current" != "$heads" ]
}

# Detecta migration destrutiva (DROP) nos arquivos de migration
has_destructive_migration() {
  local migrations_dir="${1:-backend/alembic/versions}"
  if [ -d "$migrations_dir" ]; then
    grep -rliE "drop_table|drop_column|DROP TABLE|DROP COLUMN" "$migrations_dir" 2>/dev/null | head -1
  fi
}

# ─── Deploy ──────────────────────────────────────────────────
do_deploy() {
  if [ -z "$TAG" ]; then
    err "--tag obrigatório para deploy (ex: --tag=2026-05-22-1430 ou --tag=SHA)"
    exit 1
  fi
  
  log "Deploy $APP_NAME — tag $TAG"
  echo ""
  
  # Tag anterior (para rollback)
  local prev_tag=""
  if [ -f "$TAG_STATE_FILE" ]; then
    prev_tag=$(node -p "try{JSON.parse(require('fs').readFileSync('$TAG_STATE_FILE')).current}catch(e){''}" 2>/dev/null || echo "")
  fi

  # ── 1. Pre-flight ──
  log "1. Pre-flight check"
  [ -f "$ENV_FILE" ] || { err "$ENV_FILE não existe — secrets ausentes"; [ "$DRY_RUN" = false ] && exit 1; }
  [ -f "$COMPOSE_FILE" ] || { err "$COMPOSE_FILE não existe"; [ "$DRY_RUN" = false ] && exit 1; }
  
  # Login no registry (GHCR usa GITHUB_TOKEN; em CI já vem do ambiente)
  if [ -n "${GITHUB_TOKEN:-}" ]; then
    run "echo \"\$GITHUB_TOKEN\" | docker login $REGISTRY -u \"\${GITHUB_ACTOR:-token}\" --password-stdin"
  fi
  ok "Pre-flight OK"

  # ── 2. Pull das imagens novas ──
  log "2. Pull das imagens (tag $TAG) do $REGISTRY"
  run "TAG=$TAG docker compose -f '$COMPOSE_FILE' pull"
  ok "Imagens baixadas"

  # ── 3. Backup + Migrations ANTES do switch ──
  log "3. Verificando migrations"
  if has_pending_migrations; then
    log "   Há migrations pendentes"
    
    # Backup pré-migration OBRIGATÓRIO
    local destructive
    destructive=$(has_destructive_migration || echo "")
    if [ -n "$destructive" ]; then
      warn "   Migration DESTRUTIVA detectada em: $destructive"
      warn "   Backup pré-migration é OBRIGATÓRIO antes de prosseguir"
    fi
    
    log "   Backup pré-migration pro B2..."
    if [ -x "$BACKUP_SCRIPT" ]; then
      if [ "$DRY_RUN" = false ]; then
        if ! bash "$BACKUP_SCRIPT" pre-migration; then
          err "BACKUP PRÉ-MIGRATION FALHOU — deploy ABORTADO (não migra sem backup)"
          err "Banco intocado, containers antigos continuam rodando."
          exit 1
        fi
      else
        echo "    [dry-run] bash $BACKUP_SCRIPT pre-migration"
      fi
      ok "   Backup pré-migration concluído"
    else
      err "Script de backup não encontrado/executável: $BACKUP_SCRIPT"
      err "Migration NÃO deve prosseguir sem backup. Abortando."
      exit 1
    fi
    
    # Aplicar migration (banco nativo, via container que conecta nele)
    log "   Aplicando migration (alembic upgrade head)"
    if [ "$DRY_RUN" = false ]; then
      if ! TAG=$TAG docker compose -f "$COMPOSE_FILE" run --rm api alembic upgrade head; then
        err "MIGRATION FALHOU — deploy abortado. Containers antigos seguem rodando."
        err "Banco pode estar parcialmente migrado — verifique e restaure do backup se necessário:"
        err "  bash bin/restore-mysql-b2.sh --list"
        exit 1
      fi
    else
      echo "    [dry-run] docker compose run --rm api alembic upgrade head"
    fi
    ok "   Migrations aplicadas"
  else
    ok "   Sem migrations pendentes"
  fi

  # ── 4. Switch: subir containers com novas imagens ──
  log "4. Subindo containers (tag $TAG) — graceful"
  # up -d recria só os containers cujas imagens mudaram. NUNCA -v (preservaria volumes de qualquer forma, mas -v nunca é usado)
  run "TAG=$TAG docker compose -f '$COMPOSE_FILE' up -d --remove-orphans"
  ok "Containers no ar com tag $TAG"

  # ── 5. Health check ──
  log "5. Health check"
  if [ "$DRY_RUN" = false ] && command -v curl >/dev/null 2>&1; then
    sleep 5
    local healthy=false
    for i in 1 2 3 4 5 6; do
      if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
        healthy=true
        break
      fi
      log "   tentativa $i/6 — aguardando container subir..."
      sleep 5
    done
    
    if [ "$healthy" = true ]; then
      ok "Health check OK"
    else
      # ── 6. Rollback automático ──
      err "Health check FALHOU após 30s — ROLLBACK AUTOMÁTICO"
      if [ -n "$prev_tag" ]; then
        log "   Voltando para tag anterior: $prev_tag"
        TAG=$prev_tag docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
        err "Revertido para $prev_tag. Investigar a tag $TAG."
        warn "   ATENÇÃO: se migration rodou, o schema pode estar à frente do código revertido."
        warn "   Avalie restore do backup pré-migration:"
        warn "     bash bin/restore-mysql-b2.sh --list"
      else
        err "Sem tag anterior conhecida — intervenção manual necessária"
      fi
      exit 1
    fi
  else
    warn "curl indisponível ou dry-run — health check pulado"
  fi

  # ── 7. Registrar tag atual + limpar imagens antigas ──
  log "7. Registrando estado e limpando imagens órfãs"
  if [ "$DRY_RUN" = false ]; then
    echo "{\"current\":\"$TAG\",\"previous\":\"$prev_tag\",\"deployed_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > "$TAG_STATE_FILE"
    docker image prune -f >/dev/null 2>&1 || true
  fi
  ok "Estado registrado (current=$TAG, previous=$prev_tag)"

  echo ""
  ok "Deploy $TAG concluído"
  echo "   rollback: ./deploy-docker.sh --rollback"
}

# ─── Rollback ────────────────────────────────────────────────
do_rollback() {
  local target="$ROLLBACK_TO"
  
  if [ -z "$target" ] && [ -f "$TAG_STATE_FILE" ]; then
    target=$(node -p "JSON.parse(require('fs').readFileSync('$TAG_STATE_FILE')).previous" 2>/dev/null || echo "")
  fi
  
  if [ -z "$target" ]; then
    err "Sem tag de rollback. Use --rollback-to=TAG ou garanta $TAG_STATE_FILE"
    exit 1
  fi
  
  log "ROLLBACK para tag $target"
  run "TAG=$target docker compose -f '$COMPOSE_FILE' pull"
  run "TAG=$target docker compose -f '$COMPOSE_FILE' up -d --remove-orphans"
  
  if [ "$DRY_RUN" = false ] && command -v curl >/dev/null 2>&1; then
    sleep 5
    if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
      ok "Health check OK após rollback"
      echo "{\"current\":\"$target\",\"previous\":\"\",\"rolled_back_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > "$TAG_STATE_FILE"
    else
      err "Health check falhou após rollback — intervenção manual"
      exit 1
    fi
  fi
  
  warn "Se a versão com problema rodou migration, schema pode estar à frente."
  warn "Avalie: bash bin/restore-mysql-b2.sh --list"
  ok "Rollback para $target concluído"
}

# ─── Main ────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════"
echo "GSD Docker Deploy — $APP_NAME"
echo "Banco: MySQL NATIVO na VPS (fora do Docker, intocado pelo deploy)"
[ "$DRY_RUN" = true ] && echo "(DRY RUN)"
echo "═══════════════════════════════════════════════════════"
echo ""

acquire_lock

if [ "$ROLLBACK" = true ]; then
  do_rollback
else
  do_deploy
fi
