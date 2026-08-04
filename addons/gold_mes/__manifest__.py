# -*- coding: utf-8 -*-
"""
贵金属首饰加工车间 ERP — 油压 + 失蜡铸造
=========================================

本模块为 Odoo 17 CE 定制模块,覆盖:
  - 工艺主数据(物料 / 工艺路线 / 工序 / 设备 / 工位)
  - 金料批次(0.001g 精度 / 实时金价 / 旧金回收)
  - 多阶 BOM + 生产订单 + 油压 / 失蜡双工艺路线
  - 工序报工(称重直采) + 损耗追溯 + 差异预警
  - 质检印记(GB 11887) + XRF 含量 + 模具 / 蜡模
  - 委外加工(失蜡 / 镶石 / 电镀 / 抛光 外协)
  - 件级 SN(一物一码) + 扫码追溯
  - MES REST API + 设备接入接口(OPC UA / MQTT 预留)
  - 车间看板(总看板 / 油压线 / 失蜡线 / 金料 / 质量)
  - QWeb 报告(质检 / XRF / 工序汇总 / 批次 / 委外 / 损耗追溯)

版本: gold_mes 17.0.1.0.0
适配: Odoo 17.0 CE / Python 3.11 / PostgreSQL 15
"""

{
    "name": "贵金属首饰车间 ERP — 油压 + 失蜡铸造",
    "version": "17.0.1.0.0",
    "summary": "贵金属首饰加工车间专用 ERP,聚焦工艺执行 / 金料 / 损耗 / 印记",
    "description": """
贵金属首饰加工车间 ERP
=====================

- 工艺: 油压(9 道) + 失蜡铸造(11 道)
- 金料: 0.001g 精度 + 实时金价 + 旧金回收
- 损耗: 工序级追溯 + 差异预警
- 印记: GB 11887-2012 §4.1 强制合规
- 委外: 包工包料 / 包工不包料 / 损耗分摊
- 件级 SN: 一物一码 / 扫码追溯 / NGTC 证书
- 设备: OPC UA / MQTT 接口预留
- 看板: 车间大屏 / 工位屏
- 报告: QWeb / PDF(质检 / XRF / 工序汇总 / 批次 / 委外 / 损耗追溯)
""",
    "author": "ERP-Architect-01 (赫菲斯托斯·锻金)",
    "website": "https://internal.gold-mes",
    "category": "Manufacturing",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mrp",
        "product",
        "stock",
        "uom",
    ],
    "data": [
        # 基础数据
        "security/gold_mes_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/measurement_uom_data.xml",
        "data/precious_metal_category_data.xml",
        "data/process_operation_data.xml",
        "data/process_route_template_data.xml",
        "data/shift_calendar_data.xml",
        # 视图
        "views/menus.xml",
        "views/assets.xml",
        "views/gold_material_batch_views.xml",
        "views/gold_measurement_views.xml",
        "views/gold_price_engine_views.xml",
        "views/gold_recycle_views.xml",
        "views/gold_process_route_views.xml",
        "views/gold_process_operation_views.xml",
        "views/gold_equipment_views.xml",
        "views/gold_workstation_views.xml",
        "views/gold_mold_views.xml",
        "views/gold_wax_model_views.xml",
        "views/mrp_bom_views.xml",
        "views/gold_production_order_views.xml",
        "views/gold_workorder_report_views.xml",
        "views/gold_outsource_order_views.xml",
        "views/gold_piece_views.xml",
        "views/gold_quality_views.xml",
        "views/gold_imprint_views.xml",
        "views/gold_xrf_views.xml",
        "views/gold_loss_trace_views.xml",
        "views/gold_dashboard_views.xml",
        # 报告
        "report/gold_report_templates.xml",
    ],
    "demo": [
        "demo/demo_gold_mes.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
