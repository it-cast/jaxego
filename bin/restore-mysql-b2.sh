#!/usr/bin/env bash
# restore-mysql-b2.sh — Recuperação de desastre do MySQL a partir do B2
#
# Suporta dois modos:
#   1. Restore de dump (volta ao estado de um backup diário) — RPO até 24h
#   2. Point-in-time recovery (dump + replay de binlog até instante exato) — RPO minutos
#
# RECUPERAÇÃO DE TRAGÉDIA — runbook:
#   Cenário: banco corrompido/perdido às 18h32. Último dump: 3h. Binlogs até 18h30.
#   Resultado: restaura dump das 3h + aplica binlogs até 18h30 → perde só ~2min.
#
# Uso:
#   ./restore-mysql-b2.sh --list                      # lista backups disponíveis
#   ./restore-mysql-b2.sh --dry-run --date=2026-05-22 # simula, não executa
#   ./restore-mysql-b2.sh --date=2026-05-22           # restaura dump do dia
#   ./restore-mysql-b2.sh --pitr="2026-05-22 18:30:00" # PITR até instante exato
#
# ⚠️  RESTORE SOBRESCREVE O BANCO ATUAL. Confirma 2x antes.
#
# Adicionado em v0.9.4.

set -euo pipefail

DB_NAME="${DB_NAME:-meuapp}"
DB_USER="${DB_USER:-root}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"

B2_REMOTE="${B2_REMOTE:-b2:meu-bucket-backups}"
B2_PREFIX="${B2_PREFIX:-mysql/$DB_NAME}"
LOCAL_TMP="${LOCAL_TMP:-/tmp/mysql-restore}"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${BLUE}▶${NC} $*"; }
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }

mkdir -p "$LOCAL_TMP"

DRY_RUN=false
ACTION=""
TARGET_DATE=""
PITR_TIME=""

for arg in "$@"; do
  case "$arg" in
    --list)       ACTION="list" ;;
    --dry-run)    DRY_RUN=true ;;
    --date=*)     ACTION="restore"; TARGET_DATE="${arg#*=}" ;;
    --pitr=*)     ACTION="pitr"; PITR_TIME="${arg#*=}" ;;
  esac
done

run() {
  if [ "$DRY_RUN" = true ]; then echo "    [dry-run] $*"; else eval "$@"; fi
}

# ─── list: backups disponíveis ───────────────────────────────
do_list() {
  log "Backups disponíveis no B2 ($B2_REMOTE/$B2_PREFIX)"
  echo ""
  echo "── Dumps completos (diários) ──"
  rclone lsf "$B2_REMOTE/$B2_PREFIX/full/" 2>/dev/null | sort -r | head -35 || warn "nenhum"
  echo ""
  echo "── Dumps pré-migration ──"
  rclone lsf "$B2_REMOTE/$B2_PREFIX/pre-migration/" 2>/dev/null | sort -r | head -10 || warn "nenhum"
  echo ""
  echo "── Binlogs (para PITR) ──"
  rclone lsf "$B2_REMOTE/$B2_PREFIX/binlog/" 2>/dev/null | sort -r | head -10 || warn "nenhum"
}

# ─── confirma operação destrutiva ────────────────────────────
confirm_destructive() {
  if [ "$DRY_RUN" = true ]; then return 0; fi
  echo ""
  warn "═══════════════════════════════════════════════════════"
  warn "  RESTORE VAI SOBRESCREVER O BANCO '$DB_NAME' EM $DB_HOST"
  warn "  Os dados atuais serão PERDIDOS e substituídos pelo backup."
  warn "═══════════════════════════════════════════════════════"
  echo ""
  read -rp "Digite o nome do banco para confirmar ($DB_NAME): " confirm1
  if [ "$confirm1" != "$DB_NAME" ]; then err "Cancelado."; exit 1; fi
  read -rp "Tem certeza? Digite SIM em maiúsculas: " confirm2
  if [ "$confirm2" != "SIM" ]; then err "Cancelado."; exit 1; fi
  
  # Backup de segurança do estado atual ANTES de sobrescrever
  log "Criando dump de segurança do estado ATUAL antes do restore..."
  local safety="$LOCAL_TMP/${DB_NAME}-before-restore-$(date +%Y%m%d-%H%M%S).sql.gz"
  mysqldump --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" \
    --single-transaction "$DB_NAME" 2>/dev/null | gzip > "$safety" || warn "dump de segurança falhou (banco pode já estar corrompido)"
  [ -f "$safety" ] && ok "Estado atual salvo em $safety (caso precise desfazer o restore)"
}

# ─── restore: de um dump diário ──────────────────────────────
do_restore() {
  log "Restore do dump de $TARGET_DATE"
  
  local remote_dir="$B2_REMOTE/$B2_PREFIX/full/$TARGET_DATE/"
  local dump_name
  dump_name=$(rclone lsf "$remote_dir" 2>/dev/null | head -1)
  
  if [ -z "$dump_name" ]; then
    err "Nenhum dump encontrado para $TARGET_DATE"
    err "Use --list para ver datas disponíveis"
    exit 1
  fi
  
  log "Baixando $dump_name do B2..."
  run "rclone copyto '$remote_dir$dump_name' '$LOCAL_TMP/$dump_name'"
  
  if [ "$DRY_RUN" = false ]; then
    if ! gzip -t "$LOCAL_TMP/$dump_name" 2>/dev/null; then
      err "Dump baixado está corrompido — abortando"
      exit 1
    fi
    ok "Dump íntegro"
  fi
  
  confirm_destructive
  
  log "Aplicando dump no banco..."
  run "gunzip -c '$LOCAL_TMP/$dump_name' | mysql --host='$DB_HOST' --port='$DB_PORT' --user='$DB_USER' '$DB_NAME'"
  ok "Restore concluído — banco no estado de $TARGET_DATE"
  
  [ "$DRY_RUN" = false ] && rm -f "$LOCAL_TMP/$dump_name"
}

# ─── pitr: point-in-time recovery ────────────────────────────
do_pitr() {
  log "Point-in-time recovery até: $PITR_TIME"
  
  # Data do dump base = dia do PITR (ou anterior se PITR for de madrugada)
  local pitr_date="${PITR_TIME%% *}"
  
  log "1. Restaurar dump base de $pitr_date"
  TARGET_DATE="$pitr_date"
  
  local remote_dir="$B2_REMOTE/$B2_PREFIX/full/$pitr_date/"
  local dump_name
  dump_name=$(rclone lsf "$remote_dir" 2>/dev/null | head -1)
  
  if [ -z "$dump_name" ]; then
    err "Sem dump base para $pitr_date. PITR precisa de um dump completo do dia."
    exit 1
  fi
  
  run "rclone copyto '$remote_dir$dump_name' '$LOCAL_TMP/$dump_name'"
  
  confirm_destructive
  
  log "2. Aplicar dump base"
  run "gunzip -c '$LOCAL_TMP/$dump_name' | mysql --host='$DB_HOST' --port='$DB_PORT' --user='$DB_USER' '$DB_NAME'"
  ok "Dump base aplicado"
  
  log "3. Baixar binlogs do dia para replay"
  run "rclone copy '$B2_REMOTE/$B2_PREFIX/binlog/$pitr_date/' '$LOCAL_TMP/binlogs/'"
  
  log "4. Aplicar binlogs até $PITR_TIME (replay incremental)"
  if [ "$DRY_RUN" = false ]; then
    # Descomprimir binlogs
    for bl in "$LOCAL_TMP"/binlogs/*.gz; do
      [ -f "$bl" ] && gunzip -k "$bl"
    done
    
    # mysqlbinlog com --stop-datetime aplica transações até o instante exato
    local binlog_files
    binlog_files=$(ls "$LOCAL_TMP"/binlogs/*[0-9] 2>/dev/null | sort)
    
    if [ -n "$binlog_files" ]; then
      mysqlbinlog --stop-datetime="$PITR_TIME" $binlog_files 2>/dev/null \
        | mysql --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" "$DB_NAME"
      ok "Binlogs aplicados até $PITR_TIME"
    else
      warn "Nenhum binlog encontrado — restore parou no estado do dump base"
    fi
  else
    echo "    [dry-run] mysqlbinlog --stop-datetime='$PITR_TIME' ... | mysql $DB_NAME"
  fi
  
  ok "PITR concluído — banco no estado de $PITR_TIME (perda máxima: intervalo do último binlog arquivado)"
  
  [ "$DRY_RUN" = false ] && rm -rf "$LOCAL_TMP/binlogs" "$LOCAL_TMP/$dump_name"
}

# ─── Main ────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════"
echo "MySQL Restore ← B2 — $DB_NAME"
[ "$DRY_RUN" = true ] && echo "(DRY RUN)"
echo "═══════════════════════════════════════════════════════"

case "$ACTION" in
  list)    do_list ;;
  restore) do_restore ;;
  pitr)    do_pitr ;;
  *)
    err "Especifique ação: --list | --date=YYYY-MM-DD | --pitr='YYYY-MM-DD HH:MM:SS'"
    exit 1
    ;;
esac
