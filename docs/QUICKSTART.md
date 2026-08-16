# 快速启动 — DunhuangGold-workshop-MES

## 一、环境要求

- Odoo 17.0 CE
- Python 3.11+
- PostgreSQL 15+
- 操作系统: Linux / macOS / Windows

## 二、目录结构

```
project/
├── addons/
│   └── dunhuanggold_workshop_mes/                # 主业务模块
├── scripts/
│   └── validate_dunhuanggold_workshop_mes.py    # 验证脚本
├── docs/
│   ├── DATA_MODEL.md
│   ├── API.md
│   └── QUICKSTART.md
├── seed/                        # 额外数据(可选)
├── deploy/                      # 部署
└── README.md
```

## 三、安装

### 1. 复制模块到 Odoo addons 路径

```bash
cp -r addons/dunhuanggold_workshop_mes /path/to/odoo/addons/
```

### 2. 验证模块完整性

```bash
python scripts/validate_dunhuanggold_workshop_mes.py
```

应当输出:
```
============================================================
DunhuangGold-workshop-MES — 模块验证
============================================================
[INFO] Python 语法
  OK: __init__.py
  ...
============================================================
汇总
============================================================
  ✓ Python 语法
  ✓ XML 格式
  ✓ manifest data
  ✓ access CSV
  ✓ menu action

✅ 全部检查通过
```

### 3. 在 Odoo 中安装

**方法 A: 命令行**

```bash
odoo-bin -d mydb -i dunhuanggold_workshop_mes \
  --addons-path=/path/to/addons \
  --db_host=localhost -r odoo -w odoo \
  --stop-after-init
```

**方法 B: 界面**

1. 登录 Odoo (admin/admin)
2. Settings → Users & Companies → 启用"开发者模式"
3. Apps → Update Apps List
4. 搜索 "敦煌金加工车间" → Install

### 4. 安装后配置

1. **设置 → 敦煌金加工车间**:
   - 厂印代号 (GB 11887-2012 备案)
   - NGTC 备案号
   - 损耗预警阈值 (默认 20%)
   - XRF 含量下限 (默认 99.00%)
   - 默认金价锁价时长 (默认 30 分钟)

2. **主数据 → 工艺工序**: 已有 20 个种子工序(油压 9 + 失蜡 11)

3. **主数据 → 工艺路线模板**: 已有 3 个种子路线(OWP_STD / LWC_STD / LWC_SIMPLE)

4. **主数据 → 工位**: 创建现场工位,如"油压工位"、"失蜡工位"等

5. **主数据 → 设备台账**: 注册设备
   - 油压机 / 失蜡炉 / 离心机 / 3D 打印机 / 激光焊机 / 激光打字机
   - 通讯协议(OPC UA / MQTT / RS-232)
   - IP / 端口 / 节点 ID

6. **金料与金价 → 金料批次**: 入库金料,关联供应商 + 检测证书

7. **金料与金价 → 实时金价**: 录入或 API 推送 SGE Au99.99 收盘价

## 四、典型业务流程

### 流程 1:油压订单

1. **生产订单**:Manufacturing → Manufacturing Orders → New
   - 产品: 古法金素圈戒指
   - 数量: 100
   - 工艺归属: 油压
   - 工艺路线: 油压标准 9 道
   - 模具: 古法金素圈戒指钢模
   - 确认 → 自动生成 9 个工单

2. **备料**:金料批次 → 出库 → 工艺投料
3. **油压成形**:工位扫码 → 称重直采 → 报工
4. **模具寿命**:每件报工 → 模具 `used_count` +1
5. **完工**:印记 → 质检入库

### 流程 2:失蜡订单

1. **生产订单**:产品: 18K 金钻石戒指
   - 工艺: 失蜡
   - 工艺路线: 失蜡标准 11 道 (含镶石)
   - 蜡模: 18K 钻石戒指蜡模

2. **蜡模入树**:蜡模管理 → 状态 in_tree
3. **熔金浇铸**:失蜡炉 → 投金 → 铸件 → 浇口回炉
4. **浇口回收**:作为新批次入库(回收料)
5. **执模 / 镶石 / 抛光**
6. **XRF + 印记 OCR + NGTC 证书**
7. **完工入库**

### 流程 3:旧金回收

1. **实名登记**:客户实名 + 身份证 OCR
2. **称重**:毛重 → 皮重 → 净重
3. **XRF 初检**:含量初步判定
4. **火试抽检**:精度更高(>=95% 含量差异)
5. **报价**:重量 × 含量 × 当日金价 × 折价系数
6. **客户确认** → 提纯 → 入库(回收料批次)
7. **税务**:大额(≥5万)触发 AML 报告

## 五、看板

进入 **敦煌金加工车间 → 车间看板**,可见:
- 当日完工 / 进行中 / 超耗预警 / 模具预警
- 工艺分布(油压 vs 失蜡)
- 当前金价
- 库存估值
- 7 天损耗趋势

## 六、API 调用

详见 [API.md](API.md)

### 简单示例:工序报工

```bash
curl -X POST http://localhost:8069/dunhuanggold_workshop_mes/api/v1/workorder_report \
  -H "Content-Type: application/json" \
  -d '{
    "production_id": 42,
    "operation_id": 6,
    "input_weight_g": 5.250,
    "output_weight_g": 5.180,
    "operator_id": 8,
    "work_hours": 0.45
  }'
```

## 七、运维

### Cron 任务

```python
# 刷新所有金料批次的当前金价(每 5 分钟)
model.cron_id = 'gold.price.engine.update_batch_prices'
```

### 备份

```bash
# Odoo 端
pg_dump -Fc mydb > mydb.dump

# 文件级
tar -czf addons.tar.gz addons/dunhuanggold_workshop_mes/
```

### 监控

- Prometheus 抓取 `/metrics`(需 OCA 监控模块)
- 看板 KPI: `GET /dunhuanggold_workshop_mes/api/v1/dashboard/kpi`

## 八、扩展

### 自定义工艺工序

1. 主数据 → 工艺工序 → 新建
2. 代码 / 名称 / 工艺归属 / 设备类别 / 工时定额 / 损耗定额
3. 关联到工艺路线 → 工艺路线模板

### 自定义工艺路线

1. 主数据 → 工艺路线模板 → 新建
2. 选择工艺(油压 / 失蜡)
3. 添加工序明细
4. 关联到产品

### 设备接入

1. 修改对应设备的 `protocol` / `ip_address` / `port` / `device_node_id`
2. 编写外部协议适配器(OPC UA / MQTT / RS-232)
3. 适配器调用 `POST /dunhuanggold_workshop_mes/api/v1/device/metric` 上报

### 信创环境

- 数据库:达梦 DM8 / 神通 OSCAR
- OS:麒麟 V10 / 统信 UOS
- CPU:鲲鹏 / 飞腾
- ERP:用友 YonBIP / 金蝶云·苍穹(信创版)

## 九、常见问题

### Q1:负数重量如何处理?

金料批次所有重量字段必须 >= 0,负数会触发 ValidationError。

### Q2:印记三级分离报错?

操作员 / 复核员 / 编码员三者必须不同人,优先级:`GB 11887-2012 §4.1`。

### Q3:超耗预警阈值如何调整?

设置 → 敦煌金加工车间 → 损耗预警阈值。常见 10-30%。

### Q4:旧金回收大额触发?

按"≥5万元"标准判断,触发 AML 报告字段;实际业务标准按当地法规调整。

### Q5:金料批次报废?

金料批次 → 状态 → 报废。可用重量立即归零。

## 十、版本

- 模块版本:17.0.1.0.0
- 适配:Odoo 17.0 CE
- Python 3.11+
- PostgreSQL 15+

## 十一、合规

- `GB 11887-2012`《首饰 贵金属纯度的命名及纯度规定》
- `GB/T 18043-2013`《首饰 贵金属含量的无损检测 X 射线荧光光谱法》
- `QB/T 1689-2010`《贵金属饰品术语》
- 黄金增值税即征即退(财税[2002]142号、[2008]171号、[2010]51号)
- 反洗钱(AML)

## 十二、作者

- 赫菲斯托斯·锻金 (ERP-Architect-01)
- 资深车间 ERP 架构师 / 贵金属首饰加工数字化专家
