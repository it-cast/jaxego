#!/usr/bin/env bash
# backup-mysql-b2.sh — Backup de MySQL nativo (VPS) para Backblaze B2
#
# Estratégia de recuperação de desastre:
#   - Dump diário completo (mysqldump --single-transaction, sem downtime)
#   - Binlog arquivado a cada poucos minutos (point-in-time recovery)
#   - Retenção: 30 dias de dumps diários + binlogs do período
#
# RPO (perda máxima de dados):
#   - Sem binlog: até 24h (último dump diário)
#   - Com binlog PITR: minutos (último dump + replay do binlog até o instante)
#
# Este script faz o lado do BACKUP. Para RESTORE, ver: bin/restore-mysql-b2.sh
#
# Pré-requisitos:
#   - mysqldump no PATH
#   - rclone configurado para B2 (rclone config) OU b2 CLI
#   - MySQL com log_bin ativado (para PITR) — ver seção SETUP no fim
#
# Uso:
#   ./backup-mysql-b2.sh full           # dump completo (rodar diário via cron)
#   ./backup-mysql-b2.sh binlog         # arquiva binlogs (rodar a cada 5min via cron)
#   ./backup-mysql-b2.sh prune          # remove backups > retenção
#   ./backup-mysql-b2.sh pre-migration  # dump rotulado antes de migration
#
# Adicionado em v0.9.4.

set -euo pipefail

# ─── Configuração (ADAPTAR via env ou editar) ────────────────
DB_NAME="${DB_NAME:-meuapp}"
DB_USER="${DB_USER:-backup_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
# senha vem de ~/.my.cnf (recomendado) ou MYSQL_PWD — nunca hardcoded

B2_REMOTE="${B2_REMOTE:-b2:meu-bucket-backups}"   # rclone remote
B2_PREFIX="${B2_PREFIX:-mysql/$DB_NAME}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

LOCAL_TMP="${LOCAL_TMP:-/tmp/mysql-backup}"
BINLOG_DIR="${BINLOG_DIR:-/var/lib/mysql}"        # onde MySQL grava binlogs
DATE="$(date +%Y-%m-%d)"
TIMESTAMP="$(date +%Y-%m-%d-%H%M%S)"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${BLUE}▶${NC} $*"; }
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }

mkdir -p "$LOCAL_TMP"

# Detectar ferramenta de upload (rclone preferido, b2 CLI fallback)
detect_uploader() {
  if command -v rclone >/dev/null 2>&1; then
    echo "rclone"
  elif command -v b2 >/dev/null 2>&1; then
    echo "b2"
  else
    echo "none"
  fi
}

upload_to_b2() {
  local local_file="$1"
  local remote_path="$2"
  local uploader
  uploader=$(detect_uploader)
  
  case "$uploader" in
    rclone)
      rclone copyto "$local_file" "$B2_REMOTE/$remote_path" --b2-hard-delete 2>&1
      ;;
    b2)
      b2 upload-file "${B2_REMOTE#b2:}" "$local_file" "$remote_path" 2>&1
      ;;
    none)
      err "Nenhum uploader (rclone/b2) disponível — backup local OK mas NÃO enviado ao B2"
      return 1
      ;;
  esac
}

# ─── full: dump completo diário ──────────────────────────────
do_full() {
  log "Dump completo de '$DB_NAME' (single-transaction, sem downtime)"
  
  local dump_file="$LOCAL_TMP/${DB_NAME}-full-${TIMESTAMP}.sql.gz"
  
  # --single-transaction: snapshot consistente do InnoDB sem travar escritas
  # --master-data=2: registra a posição do binlog no dump (essencial para PITR)
  # --routines --triggers --events: inclui stored procedures, triggers, events
  if mysqldump \
      --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" \
      --single-transaction \
      --master-data=2 \
      --routines --triggers --events \
      --default-character-set=utf8mb4 \
      "$DB_NAME" 2>/dev/null | gzip > "$dump_file"; then
    ok "Dump criado: $dump_file ($(du -h "$dump_file" | cut -f1))"
  else
    err "mysqldump FALHOU — backup não criado"
    rm -f "$dump_file"
    exit 1
  fi
  
  # Verificar integridade do gzip
  if ! gzip -t "$dump_file" 2>/dev/null; then
    err "Dump corrompido (gzip -t falhou) — abortando"
    rm -f "$dump_file"
    exit 1
  fi
  ok "Integridade do dump verificada"
  
  # Upload pro B2
  log "Enviando para B2: $B2_PREFIX/full/${DATE}/"
  if upload_to_b2 "$dump_file" "$B2_PREFIX/full/${DATE}/$(basename "$dump_file")"; then
    ok "Enviado ao B2"
    rm -f "$dump_file"   # limpar local após upload confirmado
  else
    warn "Upload falhou — dump mantido localmente em $dump_file"
    exit 1
  fi
  
  ok "Backup full concluído: $TIMESTAMP"
}

# ─── binlog: arquiva binlogs para PITR ───────────────────────
do_binlog() {
  log "Arquivando binlogs para point-in-time recovery"
  
  # Força flush para fechar o binlog atual e começar novo
  mysql --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" \
    -e "FLUSH BINARY LOGS;" 2>/dev/null || {
      warn "FLUSH BINARY LOGS falhou — binlog pode não estar ativado"
      warn "Ver seção SETUP no topo do script para ativar log_bin"
      exit 1
    }
  
  # Listar binlogs (exceto o ativo, que ainda está sendo escrito)
  local binlogs
  binlogs=$(mysql --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" \
    -N -e "SHOW BINARY LOGS;" 2>/dev/null | awk '{print $1}' | head -n -1)
  
  if [ -z "$binlogs" ]; then
    warn "Nenhum binlog para arquivar"
    return 0
  fi
  
  local count=0
  for binlog in $binlogs; do
    local binlog_path="$BINLOG_DIR/$binlog"
    if [ -f "$binlog_path" ]; then
      # Já arquivado? (marca local)
      if [ ! -f "$LOCAL_TMP/.archived-$binlog" ]; then
        gzip -c "$binlog_path" > "$LOCAL_TMP/${binlog}.gz"
        if upload_to_b2 "$LOCAL_TMP/${binlog}.gz" "$B2_PREFIX/binlog/${DATE}/${binlog}.gz"; then
          touch "$LOCAL_TMP/.archived-$binlog"
          rm -f "$LOCAL_TMP/${binlog}.gz"
          count=$((count + 1))
        fi
      fi
    fi
  done
  
  ok "$count binlog(s) arquivado(s) para B2"
}

# ─── pre-migration: dump rotulado antes de migration ─────────
do_pre_migration() {
  log "Dump PRÉ-MIGRATION (rede de segurança antes de alterar schema)"
  
  local dump_file="$LOCAL_TMP/${DB_NAME}-pre-migration-${TIMESTAMP}.sql.gz"
  
  if mysqldump \
      --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" \
      --single-transaction --master-data=2 \
      --routines --triggers --events \
      --default-character-set=utf8mb4 \
      "$DB_NAME" 2>/dev/null | gzip > "$dump_file"; then
    ok "Dump pré-migration criado"
  else
    err "mysqldump FALHOU — migration NÃO deve prosseguir sem backup"
    rm -f "$dump_file"
    exit 1
  fi
  
  if ! gzip -t "$dump_file" 2>/dev/null; then
    err "Dump corrompido — migration NÃO deve prosseguir"
    rm -f "$dump_file"
    exit 1
  fi
  
  # Upload com label especial — retenção maior (não removido pelo prune diário)
  if upload_to_b2 "$dump_file" "$B2_PREFIX/pre-migration/${TIMESTAMP}/$(basename "$dump_file")"; then
    ok "Dump pré-migration no B2: $B2_PREFIX/pre-migration/${TIMESTAMP}/"
    rm -f "$dump_file"
  else
    err "Upload do dump pré-migration FALHOU — migration NÃO deve prosseguir"
    exit 1
  fi
  
  # Escrever marca para o release-auditor verificar
  echo "{\"timestamp\":\"$TIMESTAMP\",\"db\":\"$DB_NAME\",\"location\":\"$B2_PREFIX/pre-migration/${TIMESTAMP}/\"}" \
    > "$LOCAL_TMP/.last-pre-migration-backup.json"
  
  ok "Backup pré-migration concluído — seguro prosseguir com migration"
}

# ─── prune: remove backups além da retenção ──────────────────
do_prune() {
  log "Removendo backups full > $RETENTION_DAYS dias (binlogs do mesmo período)"
  
  local uploader
  uploader=$(detect_uploader)
  
  if [ "$uploader" = "rclone" ]; then
    # rclone tem --min-age para deletar por idade
    rclone delete "$B2_REMOTE/$B2_PREFIX/full" --min-age "${RETENTION_DAYS}d" 2>&1 || warn "prune full falhou"
    rclone delete "$B2_REMOTE/$B2_PREFIX/binlog" --min-age "${RETENTION_DAYS}d" 2>&1 || warn "prune binlog falhou"
    # pre-migration: retenção maior (90d) — são marcos importantes
    rclone delete "$B2_REMOTE/$B2_PREFIX/pre-migration" --min-age "90d" 2>&1 || warn "prune pre-migration falhou"
    # limpar marcas locais antigas de binlog
    find "$LOCAL_TMP" -name ".archived-*" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    ok "Prune concluído (full/binlog: ${RETENTION_DAYS}d, pre-migration: 90d)"
  else
    warn "Prune automático só suportado com rclone — configure lifecycle no B2 manualmente"
  fi
}

# ─── Main ────────────────────────────────────────────────────
ACTION="${1:-full}"

echo "═══════════════════════════════════════════════════════"
echo "MySQL Backup → B2 — $DB_NAME [$ACTION]"
echo "═══════════════════════════════════════════════════════"

case "$ACTION" in
  full)          do_full ;;
  binlog)        do_binlog ;;
  pre-migration) do_pre_migration ;;
  prune)         do_prune ;;
  *)
    err "Ação desconhecida: $ACTION"
    echo "Uso: $0 [full|binlog|pre-migration|prune]"
    exit 1
    ;;
esac

# ══════════════════════════════════════════════════════════════
# SETUP (ler uma vez, configurar no servidor):
#
# 1. Usuário de backup com permissão mínima:
#    CREATE USER 'backup_user'@'localhost' IDENTIFIED BY 'senha-forte';
#    GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER, RELOAD,
#          REPLICATION CLIENT ON *.* TO 'backup_user'@'localhost';
#    FLUSH PRIVILEGES;
#
# 2. Senha em ~/.my.cnf (chmod 600), NÃO no script:
#    [client]
#    user=backup_user
#    password=senha-forte
#
# 3. Ativar binlog para PITR — em /etc/mysql/mysql.conf.d/mysqld.cnf:
#    [mysqld]
#    log_bin = /var/lib/mysql/mysql-bin
#    binlog_format = ROW
#    binlog_expire_logs_seconds = 604800   # 7 dias local (B2 guarda 30)
#    server_id = 1
#    (reiniciar mysql após editar)
#
# 4. Configurar rclone para B2:
#    rclone config
#    → n (new remote) → nome: b2 → tipo: Backblaze B2
#    → account ID + application key
#
# 5. Cron (crontab -e):
#    # dump completo diário às 3h
#    0 3 * * *   /opt/projeto/bin/backup-mysql-b2.sh full   >> /var/log/mysql-backup.log 2>&1
#    # binlog a cada 5min (PITR)
#    */5 * * * * /opt/projeto/bin/backup-mysql-b2.sh binlog >> /var/log/mysql-backup.log 2>&1
#    # prune diário às 4h
#    0 4 * * *   /opt/projeto/bin/backup-mysql-b2.sh prune  >> /var/log/mysql-backup.log 2>&1
#
# 6. TESTE o restore (backup não-testado não é backup):
#    ./restore-mysql-b2.sh --list
#    ./restore-mysql-b2.sh --dry-run --date=2026-05-22
# ══════════════════════════════════════════════════════════════
