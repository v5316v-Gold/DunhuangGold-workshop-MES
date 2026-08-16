# DunhuangGold-workshop-MES — 油压 + 失蜡铸造

> **贵金属首饰加工车间 MES**：油压 + 失蜡铸造 双工艺路线，专为贵金属行业（黄金/K金/铂金/银/钻石镶嵌）打造的人机料法环全覆盖 + 生产后闭环的制造执行系统。
---

**[English](README.md)** | 中文

---


> 车间专用 ERP,聚焦"工艺执行 + 金料消耗 + 损耗追溯 + 质检印记"。
> 范围界定:从原料接收 → 加工 → 质检入库。销售 / 财务 / 零售由下游系统衔接(预留接口)。

## 项目状态

✅ 模块骨架完成 / 0 个未解决 Lint 错误 / 5 项自动验证全部通过
✅ **人机料法环 (4M1E) 五要素全覆盖 + 生产后闭环**(环境/危化品/能耗、资质/考勤、维护/备件、SOP/ECN、盘点/成品入库/班后回料)

```
============================================================
DunhuangGold-workshop-MES — 模块验证
============================================================
  ✓ Python 语法   (46 个文件)
  ✓ XML 格式     (43 个文件)
  ✓ manifest data
  ✓ access CSV   (108 个角色权限)
  ✓ menu action  (34 个 action)

✅ 全部检查通过
```

## 技术栈

| 层 | 选型 | 备注 |
|---|---|---|
| 框架 | Odoo 17.0 CE | Python 3.11 + PostgreSQL 15 |
| 模块 | addons/dunhuang_gold_mes | 单一业务模块,深度定制 |
| DB | PostgreSQL 15 | 0.001g 重量用 NUMERIC(18,6) |
| API | Odoo HTTP Controllers | REST 形式,供 MES 工位 / 移动端调用 |
| 设备 | OPC UA / MQTT 预留接口 | python-opcua / paho-mqtt |
| 看板 | QWeb + JS + OWL | 车间大屏 / 工位屏 |
| 部署 | Docker / 物理 | 见 deploy/ |

## 核心能力

### 1. 工艺主数据
- 油压 9 道 / 失蜡 11 道 完整种子数据
- 工艺路线模板(标准 / 精简 / 含镶石 等变体)
- 工艺路线自动计算合计工时 + 损耗率(叠加公式)

### 2. 金料 & 金价
- 金料批次:NUMERIC(18,6) 精度 / 0.001g 实时称重
- 实时金价引擎:SGE / LBMA / 银行 / API 推送
- 锁价:订单报价可锁定 15min / 30min / 1h / 当日
- 旧金回收:含 XRF / 火试 / 折价 / AML 大额

### 3. 工艺执行
- 多阶 BOM(金料 BOM + 镶石 BOM + 包装 BOM + 焊料 BOM)
- 油压 vs 失蜡 双工艺路线
- 模具寿命累计 + 预警 + 自动报废
- 蜡模 3D 打印 / 银版 / 橡胶模 全生命周期

### 4. 工序报工
- 工位扫码: PDA / 工位平板 / 扫码枪
- 重量直采:电子天平 0.001g 精度
- 损耗实时计算: 实际 - 产出 = 损耗量
- 损耗率差异: > 阈值(默认 20%) 触发预警
- 工时差异: 实际 - 定额

### 5. 质量 & 印记
- 质检:重量 / 含量 / 印记 / 表面 四维度
- XRF 检测:GB/T 18043-2013 标准 / 多金属含量
- 印记:GB 11887-2012 §4.1 强制合规
- 三级分离:操作员 / 复核员 / 编码员
- OCR 校验:防止人工错误
- NGTC 证书:一物一证 + 防伪

### 6. MES REST API
11 个对外端点,覆盖:
- 工序报工 / 批次分配 / 金价推送
- 印记 OCR 校验 / XRF 检测
- 设备心跳 / 设备度量 / 设备列表
- 看板 KPI

### 7. 设备接入
- OPC UA / MQTT / Modbus / RS-232 协议预留
- 设备心跳 + 实时度量上报
- OEE 累积计算

### 8. 看板
- 当日完工 / 进行中 / 超耗预警 / 模具预警
- 工艺分布(油压 vs 失蜡)
- 当前金价 + 库存估值
- 7 天损耗趋势

### 9. 人机料法环 (4M1E) 全覆盖
- **人 (Man)**:员工资质证书矩阵 + 考勤/工时 + 资质有效期自动校验(过期停工)
- **机 (Machine)**:设备台账 + OEE + 维护工单(PM/CM/BM) + 备品备件 + 低库存预警
- **料 (Material)**:金料批次(0.001g) + 金价引擎 + 旧金回收 + 多阶 BOM + 重量平衡校验
- **法 (Method)**:工艺路线 + 模具/蜡模 + SOP 作业指导书(版本化) + ECN 工程变更审批流
- **环 (Environment)**:环境监测(温湿度/洁净度/照度/噪声/VOC/PM2.5 超限报警) + 危化品双人双锁 + 能耗分项计量

### 10. 生产后闭环
- **金料盘点单**:盘点范围 + 账面 vs 实盘 + 盘盈盘亏 + 复核审批 + 差异自动回写批次(盘亏超可用拦截)
- **成品入库单**:件级 SN 由 finished → stored 入库 + 可选生成成品批次(source=finished_goods)
- **班后回料单**:浇口/边角/抛光粉回库, 新建回料批次或回入现有批次(调用 batch.receive)

## 目录结构

```
project/
├── README.md                     # 本文件
├── addons/dunhuang_gold_mes/              # Odoo 17 业务模块
│   ├── __manifest__.py
│   ├── __init__.py
│   ├── models/                   # 35 个主模型 (人机料法环 + 生产后)
│   ├── views/                    # 26 个视图 + 菜单
│   ├── security/                 # 权限 / 角色 / 8 个角色
│   ├── data/                     # 种子数据
│   ├── demo/                     # 演示数据
│   ├── controllers/              # 27 个 REST API 端点
│   └── static/                   # 看板 JS / CSS / XML
├── scripts/
│   └── validate_dunhuang_gold_mes.py     # 5 项自动验证
├── docs/
│   ├── DATA_MODEL.md            # 模型清单 / 字段表
│   ├── API.md                   # REST API 文档
│   └── QUICKSTART.md            # 快速启动
└── deploy/                       # (后续可加)
```

## 快速验证

```bash
python scripts/validate_dunhuang_gold_mes.py
```

```
✅ 全部检查通过
```

## 在 Odoo 中安装

```bash
# 1. 复制模块
cp -r addons/dunhuang_gold_mes /path/to/odoo/addons/

# 2. 安装
odoo-bin -d mydb -i dunhuang_gold_mes --addons-path=/path/to/addons \
  --db_host=localhost -r odoo -w odoo --stop-after-init

# 3. 启动
odoo-bin -d mydb --addons-path=/path/to/addons
```

详见 [docs/QUICKSTART.md](docs/QUICKSTART.md)。

## 核心数据模型

详见 [docs/DATA_MODEL.md](docs/DATA_MODEL.md)。

主模型:
- `gold.material.batch` - 金料批次
- `gold.price.engine` - 实时金价
- `gold.process.operation` - 工艺工序
- `gold.process.route` - 工艺路线
- `gold.equipment` - 设备台账
- `gold.workorder.report` - 工序报工
- `gold.loss.trace` - 损耗追溯
- `gold.imprint` - 印记
- `gold.xrf.record` - XRF 检测
- `gold.mold` / `gold.wax.model` - 模具 / 蜡模
- `gold.recycle` - 旧金回收
- `gold.quality.inspection` - 质检
- `gold.employee.certificate` / `gold.work.attendance` - 员工资质 / 考勤 (人)
- `gold.maintenance.order` / `gold.spare.part` - 维护工单 / 备件 (机)
- `gold.sop.document` / `gold.ecn` - SOP / 工程变更 (法)
- `gold.environment.reading` / `gold.hazardous.chemical` / `gold.energy.reading` - 环境 / 危化品 / 能耗 (环)
- `gold.inventory.count` - 金料盘点单 (生产后)
- `gold.finished.goods` - 成品入库单 (生产后)
- `gold.material.return` - 班后回料单 (生产后)

## REST API

详见 [docs/API.md](docs/API.md)。

27 个端点:
- `POST /dunhuang_gold_mes/api/v1/login`
- `GET /dunhuang_gold_mes/api/v1/production/{id}`
- `GET /dunhuang_gold_mes/api/v1/workorder/by_station/{station_id}`
- `POST /dunhuang_gold_mes/api/v1/workorder_report`
- `GET /dunhuang_gold_mes/api/v1/batch/{batch_no}`
- `POST /dunhuang_gold_mes/api/v1/batch/allocate`
- `GET /dunhuang_gold_mes/api/v1/price/current`
- `POST /dunhuang_gold_mes/api/v1/price/push`
- `POST /dunhuang_gold_mes/api/v1/imprint/verify`
- `POST /dunhuang_gold_mes/api/v1/xrf/save`
- `GET /dunhuang_gold_mes/api/v1/dashboard/kpi`
- `POST /dunhuang_gold_mes/api/v1/device/heartbeat`
- `POST /dunhuang_gold_mes/api/v1/device/metric`
- `GET /dunhuang_gold_mes/api/v1/device/list`
- `POST /dunhuang_gold_mes/api/v1/environment/reading` (环)
- `GET /dunhuang_gold_mes/api/v1/environment/latest` (环)
- `GET /dunhuang_gold_mes/api/v1/environment/alarms` (环)
- `GET /dunhuang_gold_mes/api/v1/hazchem/list` (环)
- `POST /dunhuang_gold_mes/api/v1/hazchem/issue` (环)
- `POST /dunhuang_gold_mes/api/v1/energy/reading` (环)
- `POST /dunhuang_gold_mes/api/v1/maintenance/order` (机)
- `GET /dunhuang_gold_mes/api/v1/maintenance/list` (机)
- `GET /dunhuang_gold_mes/api/v1/certificate/verify` (人)
- `POST /dunhuang_gold_mes/api/v1/inventory/count` (生产后)
- `GET /dunhuang_gold_mes/api/v1/inventory/list` (生产后)
- `POST /dunhuang_gold_mes/api/v1/finished_goods/post` (生产后)
- `POST /dunhuang_gold_mes/api/v1/material_return/confirm` (生产后)

## 工艺范围

| 工艺 | 工序数 | 关键损耗节点 |
|---|---|---|
| 油压(冲压) | 9 道 | 落料 0.5% / 切边 1-2% / 试模 5% / 执模 3-5% / 抛光 1-2% |
| 失蜡铸造 | 11 道 | 蜡模 1-2% / 熔金 5-15% / 铸件缺陷 5% / 执模 3-8% / 抛光 1-3% |

> 损耗定额按车间实测校准,本文给出经验值范围。

## 法规依据

- `GB 11887-2012`《首饰 贵金属纯度的命名及纯度规定》§4.1 印记
- `GB/T 18043-2013`《首饰 贵金属含量的无损检测 X 射线荧光光谱法》
- `QB/T 1689-2010`《贵金属饰品术语》
- 黄金交易增值税即征即退(财税[2002]142号、[2008]171号、[2010]51号)
- 反洗钱(AML)

## 角色与权限

8 个角色,细粒度权限控制:
- 车间操作员 (员 / 工位)
- 车间班组长 (派工 / 报工)
- 车间主任 (全面管理 / KPI)
- 质检员 (印记 / XRF / 含量)
- 金库仓管员 (出入库 / 盘点)
- 设备维护员 (备件 / 校准 / 维护工单)
- 环境安全员 EHS (环境监测 / 危化品双人双锁 / 能耗)
- 数据记录 108 个权限条目

## 后续可深入

- 选型决策 SAP / Oracle / 用友 / 金蝶 / 珠宝专项
- 多阶 BOM 详解
- 工序级金料成本核算
- NGTC 一物一证对接
- 区块链溯源
- AI 视觉质检(XRF 谱图 / 表面缺陷)
- 套保分析

## 作者

**赫菲斯托斯·锻金**(ERP-Architect-01)
资深车间 ERP 架构师 / 贵金属首饰加工数字化专家
