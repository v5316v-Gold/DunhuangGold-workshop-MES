# 变更日志 (Changelog)

本项目所有重要变更记录于此。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### Changed
- **项目重命名**: 敦煌金加工车间 ERP → **DunhuangGold-workshop-MES**
  - README.zh-CN.md / README.en.md / ui_preview/README.md 标题与正文同步
  - Odoo 模块名 `dunhuanggold_workshop_mes` 保持不变 (技术标识)
  - GitHub 仓库名 `Dunhuang-workshop-ERP` 保持不变 (需在 GitHub Settings 重命名后再同步 remote)
- README.en.md: 标题 DunhuangGold-workshop-MES

### Changed
- 项目重命名: 贵金属首饰车间 ERP → **敦煌金加工车间 ERP**
  - 模块名 gold_mes → dunhuang_gold_mes
  - 命名空间 / API 路径 / 验证脚本同步
- README.en.md: 标题 Dunhuang Gold Workshop ERP

### 计划
- NGTC 一物一证 API 集成
- OPC UA 设备适配器 demo
- AI 视觉质检 POC
- 微信 / 钉钉 通知 Webhook

## [17.0.1.0.0] - 2026-08-05

### ✨ Added (新增)
- **工艺主数据**: 工艺工序 20 道(油压 9 + 失蜡 11 + 共用)、工艺路线模板 3 套(OWP_STD / LWC_STD / LWC_SIMPLE)、工位 / 设备台账
- **金料与金价**: 金料批次(NUMERIC 18,6 / 0.001g 精度)、实时金价引擎(SGE / LBMA / 银行 / API)、旧金回收(AML 大额)
- **生产执行**: 多阶 BOM、生产订单(锁价)、工单、工序报工(天平直采)、损耗追溯
- **质量**: 质检 (GB 11887-2012)、XRF 检测 (GB/T 18043-2013)、印记三级分离
- **委外加工**: 失蜡 / 镶石 / 电镀 / 抛光,包工包料 / 包工不包料,损耗分摊
- **件级 SN**: 一物一码 + 扫码追溯 + NGTC 证书
- **看板**: 车间大屏 / KPI 实时 / 工艺分布 / 损耗趋势
- **报告**: QWeb PDF 6 个(质检 / XRF / 工序汇总 / 批次 / 委外 / 损耗追溯)
- **MES REST API**: 14 个端点(报工 / 批次 / 金价 / 印记 / XRF / 设备心跳)
- **部署**: Docker / docker-compose / systemd / nginx 配置
- **测试**: 35 个核心算法单元测试(100% 通过)
- **文档**: README / DATA_MODEL / API / QUICKSTART

### 🔧 Changed (变更)
- 无

### 🐛 Fixed (修复)
- 无

### 🗑️ Deprecated (弃用)
- 无

### ❌ Removed (移除)
- 无

### 🔒 Security (安全)
- 印记三级分离: 操作员 / 复核员 / 编码员 不可兼任
- 金料批次: 重量平衡校验(差异 > 0.005g 触发异常)
- 旧金回收: AML 阈值监控(≥ 5 万自动标记)

---

## 版本说明

- **主版本号**: Odoo 大版本 (17.0)
- **次版本号**: 功能重大变更 (1)
- **修订号**: 增量发布 (0)
- **构建号**: 内部版本 (0)

### 兼容性
- Odoo 17.0 CE / Enterprise
- Python 3.11+
- PostgreSQL 15+
- 浏览器: Chrome 100+ / Edge 100+ / Firefox 100+

### 已知限制
- 设备协议适配器(OPC UA / MQTT / Modbus)仅预留接口,需现场实施
- 区块链溯源接口预留,未对接实际平台
- AI 视觉质检(XRF 谱图 / 表面缺陷)未集成,需独立 AI 服务
- 端到端测试仅覆盖核心算法,Odoo 模型层需在真实环境验证

### 性能基准
- 单条工序报工 API 响应: < 200ms
- 看板 KPI 加载: < 500ms
- 35 个核心算法测试: 0.001s
