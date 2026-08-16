# ui_preview 架构梳理

> 文档化时间：今天（动态交互 + 点击修复后）
> 范围：`ui_preview/` 全部前端 + Mock 后端的树状结构

---

## 一、总体架构树状图

```
DunhuangGold-workshop-MES — ui_preview
│
├── 1. 入口层 (HTML/CSS, 零依赖)
│   ├── index.html                          # 单页骨架 (navbar + sidebar + main)
│   │   └── 加载顺序: api.js → renderers.js → app.js
│   └── assets/css/common.css                # Odoo 17 风格样式 + 贵金属金色主题
│
├── 2. 服务层 (Node.js 内置模块, 零依赖)
│   └── ui_preview/server.js                 # 静态 + Mock REST API 一体
│       ├── 静态文件服务 (pages/*.html, assets/*)
│       │   └── Cache-Control: no-store, no-cache, must-revalidate
│       └── Mock REST API (/api/v1/*)
│           ├── 业务端点 27 个 (字段对齐 Odoo controller 契约)
│           └── 列表端点 (前端动态渲染用, 等价 Odoo search/read)
│
├── 3. 数据层 (内存 mock, 重启重置)
│   └── ui_preview/mock-data.js
│       ├── batches                          # 金料批次 (6)
│       ├── equipment                        # 设备 (4)
│       ├── workorderReports                 # 工序报工 (5)
│       ├── environmentSensors + Readings    # 环境 (6 + 6)
│       ├── hazardousChemicals               # 危化品 (4)
│       ├── maintenanceOrders + spareParts   # 维护 + 备件 (4 + 4)
│       ├── inventoryCounts + finishedGoods + materialReturns  # 生产后
│       ├── certificates + attendance         # 人员
│       ├── energyMeters                     # 能耗
│       ├── sops + ecns                      # 法
│       └── computeKpi()                     # 看板聚合
│
├── 4. 前端核心 JS (浏览器全局)
│   ├── assets/js/api.js
│   │   ├── apiGet / apiPost                 # fetch 封装
│   │   └── window.API = { get, post }
│   │   ├── escapeHtml / badge / stateBadge  # UI 通用工具
│   │   ├── num / money                     # 格式化
│   │   ├── kpiCards / renderTable          # 渲染辅助
│   │   ├── pageHeader / notice / toast
│   │   └── window.UI = { 上述全部 }
│   │
│   ├── assets/js/renderers.js
│   │   └── window.RENDERERS = { 16 个 pageId → async(main) }
│   │       ├── dashboard, material_batch, workorder_report
│   │       ├── inventory_count, material_return, finished_goods
│   │       ├── equipment, environment, hazardous_chemical, energy
│   │       ├── maintenance, spare_part
│   │       ├── certificate, attendance
│   │       └── sop, ecn
│   │
│   └── assets/js/app.js
│       ├── NAV                              # 32 个页面定义 (按业务分组)
│       ├── navigate / loadPage / renderMenu
│       ├── updateBreadcrumb / toggleSidebar
│       └── DOMContentLoaded → 绑定菜单点击 + 加载当前页
│
└── 5. 页面与渲染器 (按业务域, 32 页)
    │
    ├── 5.1 主数据 (7 页)
    │   ├── measurement       [静态]
    │   ├── process_operation [静态]
    │   ├── process_route     [静态]
    │   ├── workstation       [静态]
    │   ├── equipment         ★ 动态 RENDERERS.equipment
    │   ├── sop               ★ 动态 RENDERERS.sop
    │   └── ecn               ★ 动态 RENDERERS.ecn
    │
    ├── 5.2 人员与资质 (2 页)
    │   ├── certificate       ★ 动态 RENDERERS.certificate
    │   └── attendance        ★ 动态 RENDERERS.attendance
    │
    ├── 5.3 金料与金价 (5 页)
    │   ├── material_batch    ★ 动态 RENDERERS.material_batch
    │   ├── price_engine      [静态]
    │   ├── recycle           [静态]
    │   ├── inventory_count   ★★ 动态+表单 RENDERERS.inventory_count
    │   └── material_return   ★★ 动态+表单 RENDERERS.material_return
    │
    ├── 5.4 模具/蜡模 (2 页, 暂未动态化)
    │   ├── mold              [静态]
    │   └── wax               [静态]
    │
    ├── 5.5 设备维护 (2 页)
    │   ├── maintenance       ★★ 动态+表单 RENDERERS.maintenance
    │   └── spare_part        ★ 动态 RENDERERS.spare_part
    │
    ├── 5.6 生产执行 (5 页)
    │   ├── workorder_report  ★★ 动态+表单 RENDERERS.workorder_report
    │   ├── loss_trace        [静态]
    │   ├── outsource         [静态]
    │   ├── piece             [静态]
    │   └── finished_goods    ★★ 动态+表单 RENDERERS.finished_goods
    │
    ├── 5.7 质量与印记 (3 页, 暂未动态化)
    │   ├── qc                [静态]
    │   ├── xrf               [静态]
    │   └── imprint           [静态]
    │
    ├── 5.8 环境与安全 (3 页)
    │   ├── environment       ★★ 动态+上报 RENDERERS.environment
    │   ├── hazardous_chemical ★★ 动态+领用 RENDERERS.hazardous_chemical
    │   └── energy            ★ 动态 RENDERERS.energy
    │
    ├── 5.9 看板 (1 页)
    │   └── dashboard         ★ 动态 RENDERERS.dashboard (默认页)
    │
    └── 5.10 采购/销售预留 (2 页)
        ├── procurement       [静态]
        └── sale              [静态]
```

---

## 二、渲染能力矩阵

| 页面 | 动态渲染 | 表单交互 | POST 端点 |
|------|----------|----------|-----------|
| dashboard | ✓ | — | — |
| material_batch | ✓ | — | — |
| **workorder_report** | ✓ | **报工录入** | `/workorder_report` |
| **inventory_count** | ✓ | **新建盘点** | `/inventory/count` |
| **material_return** | ✓ | **回料录入** | `/material_return/confirm` |
| **finished_goods** | ✓ | **SN 扫码入库** | `/finished_goods/post` |
| equipment | ✓ | — | — |
| **environment** | ✓ | **读数上报** | `/environment/reading` |
| **hazardous_chemical** | ✓ | **领用出库** | `/hazchem/issue` |
| energy | ✓ | — | — |
| **maintenance** | ✓ | **新建工单** | `/maintenance/order` |
| spare_part | ✓ | — | — |
| certificate | ✓ | — | — |
| attendance | ✓ | — | — |
| sop | ✓ | — | — |
| ecn | ✓ | — | — |

**统计**：32 页中 **16 页已动态化**（带 ★/★★），其中 **8 页带表单交互**（带 ★★）。

---

## 三、页面加载与渲染时序

```
浏览器打开 http://localhost:8080/
        │
        ▼
DOMContentLoaded → app.js 初始化
        │
        ├── renderMenu()  渲染侧边栏
        ├── navigate("dashboard")
        │       │
        │       ▼
        │   loadPage("dashboard")
        │       │
        │       ├── fetch pages/page_dashboard.html → 片段 HTML
        │       ├── main.innerHTML = html              (先放静态片段)
        │       └── await RENDERERS.dashboard(main)    (再覆盖为动态渲染)
        │               │
        │               ▼
        │           apiGet("/dashboard/kpi") → {ok, data}
        │               │
        │               ▼
        │           main.innerHTML = pageHeader + kpiCards + notice  (完全覆盖)
        │               │
        │               ▼
        │           (带表单页面: 渲染 <form>, 绑定 onclick)
        │
        ▼
用户点击菜单 → navigate(newId) → loadPage(newId) → 重复上述流程
```

---

## 四、Mock API 端点清单

### 4.1 业务端点（27，对齐 Odoo controller）

| 类别 | 端点 |
|------|------|
| 认证 | `POST /api/v1/login` |
| 生产 | `GET /api/v1/production/{id}`、`GET /api/v1/workorder/by_station/{station_id}` |
| 报工 | `POST /api/v1/workorder_report` |
| 金料 | `GET /api/v1/batch/{batch_no}`、`POST /api/v1/batch/allocate` |
| 金价 | `GET /api/v1/price/current`、`POST /api/v1/price/push` |
| 质检 | `POST /api/v1/imprint/verify`、`POST /api/v1/xrf/save` |
| 看板 | `GET /api/v1/dashboard/kpi` |
| 设备 | `POST /api/v1/device/heartbeat`、`POST /api/v1/device/metric`、`GET /api/v1/device/list` |
| 环境 | `POST /api/v1/environment/reading`、`GET /api/v1/environment/latest`、`GET /api/v1/environment/alarms` |
| 危化品 | `GET /api/v1/hazchem/list`、`POST /api/v1/hazchem/issue` |
| 能耗 | `POST /api/v1/energy/reading` |
| 维护 | `POST /api/v1/maintenance/order`、`GET /api/v1/maintenance/list` |
| 资质 | `GET /api/v1/certificate/verify` |
| 盘点 | `POST /api/v1/inventory/count`、`GET /api/v1/inventory/list` |
| 入库 | `POST /api/v1/finished_goods/post`、`GET /api/v1/finished_goods/list` |
| 回料 | `POST /api/v1/material_return/confirm`、`GET /api/v1/material_return/list` |

### 4.2 列表端点（前端动态渲染专用）

`GET /api/v1/{batch|workorder_report|spare_part|energy|finished_goods|material_return|certificate|attendance|sop|ecn}/list`

---

## 五、切换真实 Odoo 后端

仅需修改 `assets/js/api.js`：

```js
const API_BASE = 'https://your-odoo.example.com/dunhuang_gold_mes/api/v1';
```

接口契约已对齐 Odoo controllers，无需改前端逻辑。

---

## 六、迭代建议（未动态化页面）

下列 8 个页面仍为静态（**★★ 已标记但暂未动态化**），可按需扩展 renderer：

| 分组 | 页面 | 优先级 |
|------|------|--------|
| 主数据 | measurement、process_operation、process_route、workstation | 低（字典类，变动少） |
| 金料 | price_engine、recycle | 中（需对接实时金价） |
| 模具 | mold、wax | 低 |
| 生产 | loss_trace、outsource、piece | 中（核心生产数据） |
| 质量 | qc、xrf、imprint | 中（质检流程） |
| 预留 | procurement、sale | 低（接口未实现） |

每个页面补一个 renderer + 1 个列表 API 即可（平均 30 行代码 + 1 个 mock 端点）。