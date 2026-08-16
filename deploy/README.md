# DunhuangGold-workshop-MES — 部署指南

## 一、Docker 部署(推荐)

### 1. 前置条件

- Docker 24+
- Docker Compose v2+
- 8 GB+ 内存 / 4 核+ CPU
- 100 GB+ 磁盘

### 2. 部署步骤

```bash
# 1. 检出代码
git clone https://github.com/your-org/dunhuang-gold-mes.git
cd dunhuang-gold-mes

# 2. 配置环境变量
cat > .env << 'EOF'
POSTGRES_PASSWORD=YourSecurePwd
ODOO_ADMIN_PWD=YourAdminPwd
EOF

# 3. 启动
docker-compose -f deploy/docker/docker-compose.yml up -d

# 4. 查看日志
docker-compose -f deploy/docker/docker-compose.yml logs -f odoo

# 5. 访问
http://localhost:8069
admin / YourAdminPwd
```

### 3. 第一次启动

- 自动初始化数据库 `dunhuanggold_workshop_mes`
- 自动安装 `dunhuanggold_workshop_mes` 模块
- 自动创建演示数据(如 demo 启用)

### 4. 访问

- Odoo 主界面:http://localhost
- 看板(OWL):http://localhost/dunhuanggold_workshop_mes
- MES REST API:http://localhost/dunhuanggold_workshop_mes/api/v1/...

### 5. 备份

- 自动备份:每天凌晨 2 点,保留 7 天 / 12 周 / 12 月
- 备份路径:`./backups/`(容器内 `/backups/`)
- 备份格式:`dunhuanggold_workshop_mes_YYYYMMDD_HHMMSS.dump`(PostgreSQL 自定义格式)

```bash
# 手动备份
docker-compose exec postgres pg_dump -U odoo -Fc dunhuanggold_workshop_mes > my_backup.dump

# 恢复
docker-compose exec -T postgres pg_restore -U odoo -d dunhuanggold_workshop_mes --clean < my_backup.dump
```

### 6. 升级

```bash
# 1. 拉取新代码
git pull

# 2. 重新构建
docker-compose build odoo

# 3. 重启
docker-compose up -d

# 4. 升级模块
docker-compose exec odoo odoo -u dunhuanggold_workshop_mes -d dunhuanggold_workshop_mes --stop-after-init
```

## 二、systemd 部署(物理机)

### 1. 安装 Odoo 17

```bash
# Ubuntu / Debian
wget -O - https://nightly.odoo.com/odoo.key | apt-key add -
echo "deb http://nightly.odoo.com/17.0/nightly/deb/ ./" >> /etc/apt/sources.list.d/odoo.list
apt-get update
apt-get install -y odoo

# 安装 PostgreSQL
apt-get install -y postgresql-15
```

### 2. 复制模块

```bash
cp -r addons/dunhuanggold_workshop_mes /usr/lib/python3/dist-packages/odoo/addons/
chown -R odoo:odoo /usr/lib/python3/dist-packages/odoo/addons/dunhuanggold_workshop_mes
```

### 3. 配置

```bash
cp deploy/systemd/odoo.service /etc/systemd/system/
cp deploy/systemd/odoo.conf /etc/odoo/odoo.conf
cp deploy/systemd/odoo-backup.timer /etc/systemd/system/
cp deploy/systemd/odoo-backup.service /etc/systemd/system/
cp deploy/systemd/odoo-backup.sh /usr/local/bin/
chmod +x /usr/local/bin/odoo-backup.sh
```

### 4. 启动

```bash
systemctl daemon-reload
systemctl enable --now odoo
systemctl enable --now odoo-backup.timer
systemctl status odoo
```

### 5. 安装模块

```bash
sudo -u odoo odoo -d dunhuanggold_workshop_mes -i dunhuanggold_workshop_mes --stop-after-init
```

## 三、监控

### 1. 健康检查

```bash
curl http://localhost:8069/web/health
```

### 2. Prometheus 监控

参考 `monitoring/prometheus.yml`(后续扩展)

### 3. 看板 KPI

```bash
curl http://localhost:8069/dunhuanggold_workshop_mes/api/v1/dashboard/kpi
```

## 四、生产加固

### 1. HTTPS

启用 nginx 443 端口 + Let's Encrypt:

```bash
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com
```

### 2. 防火墙

```bash
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 8069/tcp  # 禁止直连 Odoo
ufw deny 5432/tcp  # 禁止直连 PostgreSQL
```

### 3. 等保 2.0

- TLS 1.3
- 双因素认证
- 审计日志
- 数据加密

### 4. 国密改造

替换为国密算法:
- `SM2` 替代 RSA
- `SM3` 替代 SHA256
- `SM4` 替代 AES

## 五、迁移

### 1. 数据迁移

```bash
# 备份源
docker exec -t postgres pg_dump -U odoo -Fc dunhuanggold_workshop_mes > source.dump

# 恢复目标
docker exec -i postgres pg_restore -U odoo -d dunhuanggold_workshop_mes --clean < source.dump
```

### 2. 模块迁移

```bash
# 复制 addons/dunhuanggold_workshop_mes/
rsync -az addons/dunhuanggold_workshop_mes/ target:/usr/lib/python3/dist-packages/odoo/addons/dunhuanggold_workshop_mes/
```

## 六、常见问题

### Q1:启动后中文乱码?

确认 `LANG=zh_CN.UTF-8` 已设置,Docker 镜像已安装中文字体。

### Q2:金料批次重量 decimal 精度?

NUMERIC(18,6) = 18 位整数 + 6 位小数 = 0.001g 精度。

### Q3:金价 API 推送?

```bash
curl -X POST http://localhost:8069/dunhuanggold_workshop_mes/api/v1/price/push \
  -u user:pass \
  -d '{"price_close": 582.5, "gold_type": "au9999", "source": "sge"}'
```

### Q4:设备接入?

参考 `docs/API.md` 的 `/dunhuanggold_workshop_mes/api/v1/device/metric` 端点。
OPC UA / MQTT / RS-232 适配器示例:

```python
# MQTT 适配器示例
import paho.mqtt.client as mqtt
import requests

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload)
    requests.post(
        "http://odoo:8069/dunhuanggold_workshop_mes/api/v1/device/metric",
        json=payload,
        auth=("admin", "pwd"),
    )

client = mqtt.Client()
client.on_message = on_message
client.connect("emqx", 1883)
client.subscribe("dunhuanggold_workshop_mes/device/+/metric")
client.loop_forever()
```

## 七、版本

- Odoo 17.0 CE
- PostgreSQL 15
- Python 3.11
- Docker 24+
- 模块版本:17.0.1.0.0
