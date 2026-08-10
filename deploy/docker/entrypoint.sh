#!/bin/bash
# Odoo 容器入口 - 等待 PostgreSQL 就绪 + 模块初始化
set -e

echo "[INFO] 等待 PostgreSQL 就绪..."
until pg_isready -h "$HOSTNAME" -p 5432 -U odoo; do
  sleep 2
done

echo "[INFO] PostgreSQL 就绪"

# 第一次启动时初始化
if [ ! -f /mnt/odoo/.initialized ]; then
  echo "[INFO] 首次启动: 初始化数据库..."

  odoo \
    --db_host=postgres \
    --db_port=5432 \
    --db_user=odoo \
    --db_password=odoo \
    --db_name=dunhuang_gold_mes \
    --addons-path=/mnt/odoo/addons \
    --init=base,dunhuang_gold_mes \
    --stop-after-init \
    --without-demo=False

  touch /mnt/odoo/.initialized
  echo "[INFO] 初始化完成"
fi

# 正常启动
echo "[INFO] 启动 Odoo..."
exec odoo \
  --db_host=postgres \
  --db_port=5432 \
  --db_user=odoo \
  --db_password=odoo \
  --db_name=dunhuang_gold_mes \
  --addons-path=/mnt/odoo/addons \
  --config=/etc/odoo/odoo.conf
