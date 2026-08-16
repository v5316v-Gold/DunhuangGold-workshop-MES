#!/bin/bash
# Odoo 数据库自动备份脚本
# 保留: 每天 7 天 / 每周 12 周 / 每月 12 月

set -e

BACKUP_DIR="/var/backups/odoo"
DB_NAME="${DB_NAME:-dunhuanggold_workshop_mes}"
DB_USER="${DB_USER:-odoo}"
DB_HOST="${DB_HOST:-localhost}"
RETENTION_DAILY=7
RETENTION_WEEKLY=12
RETENTION_MONTHLY=12

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DOW=$(date +%u)
DOM=$(date +%d)

# 备份
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.dump"
pg_dump -h "$DB_HOST" -U "$DB_USER" -Fc "$DB_NAME" > "$BACKUP_FILE"

# 加密(AES-256, 可选)
# gpg --batch --yes --passphrase-file /etc/odoo/backup.gpg -c "$BACKUP_FILE"
# rm "$BACKUP_FILE"

# 上传到远端(可选)
# rsync -az "$BACKUP_FILE" backup@nas:/odoo/

# 清理
echo "[INFO] 备份完成: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

# 日级: 保留最新 7 天
find "$BACKUP_DIR" -name "${DB_NAME}_*_*.dump" -mtime +$RETENTION_DAILY -delete

# 周级: 每月 1 日全量保留
if [ "$DOM" = "01" ]; then
  cp "$BACKUP_FILE" "$BACKUP_DIR/${DB_NAME}_monthly_${TIMESTAMP}.dump"
  find "$BACKUP_DIR" -name "${DB_NAME}_monthly_*.dump" -mtime +$((RETENTION_MONTHLY * 30)) -delete
fi

# 周级: 周日备份保留
if [ "$DOW" = "7" ]; then
  cp "$BACKUP_FILE" "$BACKUP_DIR/${DB_NAME}_weekly_${TIMESTAMP}.dump"
  find "$BACKUP_DIR" -name "${DB_NAME}_weekly_*.dump" -mtime +$((RETENTION_WEEKLY * 7)) -delete
fi

echo "[INFO] 清理完成"
