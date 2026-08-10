# 敦煌金加工车间 ERP - 离线 UI 预览

纯 HTML + CSS + JS 模拟 Odoo 17 风格界面,展示车间 ERP 项目的所有核心页面。

## 启动方式

### 方式 1: Python HTTP 服务器(推荐)

```bash
cd ui_preview
python -m http.server 8080
```

然后浏览器打开:<http://localhost:8080>

### 方式 2: Node.js

```bash
cd ui_preview
npx http-server -p 8080
```

### 方式 3: 直接打开 file://

```bash
# Windows
start index.html
```

> 注意: 直接打开 `file://` 时,fetch `pages/*` 可能受同源限制,推荐用 HTTP 服务器。

## 页面清单(19 个)

| 分类 | 页面 | 文件 |
|------|------|------|
| 主数据 | 计量单位 | page_measurement.html |
| 主数据 | 工艺工序 | page_process_operation.html |
| 主数据 | 工艺路线模板 | page_process_route.html |
| 主数据 | 工位 | page_workstation.html |
| 主数据 | 设备台账 | page_equipment.html |
| 金料 | 金料批次 | page_material_batch.html |
| 金料 | 实时金价 | page_price_engine.html |
| 金料 | 旧金回收 | page_recycle.html |
| 模具 | 模具台账 | page_mold.html |
| 模具 | 蜡模管理 | page_wax_model.html |
| 生产 | 工序报工 | page_workorder_report.html |
| 生产 | 损耗追溯 | page_loss_trace.html |
| 生产 | 委外加工 | page_outsource.html |
| 生产 | 件级 SN | page_piece.html |
| 质量 | 质检记录 | page_quality.html |
| 质量 | XRF 含量检测 | page_xrf.html |
| 质量 | 印记记录 | page_imprint.html |
| 看板 | 车间看板 | page_dashboard.html |
| 预留 | 采购订单 | page_procurement.html |
| 预留 | 销售订单 | page_sale.html |

## UI 风格

- Odoo 17 风格:紫色 #714B67 + 灰色 #F8F9FA
- 贵金属主题:金色 #B8860B 强调
- 响应式:支持 768px 以下移动端
- 看板(KPI):大型数字 + 颜色编码
- 表格:数字右对齐 + tabular-nums

## 与 Odoo 的差异

| 维度 | Odoo 17 | 本预览 |
|------|---------|--------|
| 数据 | 数据库 | 静态 HTML |
| 操作 | 表单提交 | 视觉展示 |
| 权限 | 多角色 | 单一入口 |
| 实时 | 推送 | 静态 |
| 报表 | PDF/Excel | 静态展示 |

## 后续可补充

- API 接入:用真实数据填充
- 主题切换:深色模式
- 国际化:多语言
- 移动端:扫码 PDA 界面
