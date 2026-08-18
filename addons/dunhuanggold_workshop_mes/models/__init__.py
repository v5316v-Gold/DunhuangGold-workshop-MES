# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 业务模型入口
按依赖顺序加载,避免循环引用:
  1. 主数据:计量 / 工序 / 工艺路线模板 / 设备 / 工位
  2. 物料与金料:物料分类 / 金料批次 / 金价 / 旧金回收
  3. 工艺:路线 / 模具 / 蜡模
  4. 生产:BOM / 生产订单 / 工单 / 报工
  5. 质量:质检 / 印记 / XRF
  6. 委外:外协订单
  7. 件级 SN:一物一码
  8. 看板 / 设备接入
"""

# 主数据
from . import res_company
from . import res_config_settings
from . import gold_measurement
from . import gold_process_operation
from . import gold_process_route
from . import gold_equipment
from . import gold_workstation

# 物料与金料
from . import product_category
from . import product_template
from . import gold_material_batch
from . import gold_price_engine
from . import gold_recycle

# 工艺
from . import gold_mold
from . import gold_wax_model
from . import mrp_bom
from . import mrp_routing

# 生产
from . import mrp_production
from . import mrp_workorder
from . import gold_workorder_report
from . import gold_loss_trace

# 质量
from . import gold_quality_inspection
from . import gold_imprint
from . import gold_xrf_record

# 委外
from . import gold_outsource_order

# 件级 SN
from . import gold_piece
from . import gold_piece_flow_card  # Phase 3.1: 工序间交接卡

# ---- Phase 3.2: NCR 不合格品处理 ----
from . import gold_ncr

# ---- Phase 3.3: 包装 ----
from . import gold_package

# ---- 人机料法环补全 (作业指导书) ----
# 人 (Man): 资质证书 / 考勤工时
from . import gold_employee
# 机 (Machine): 维护工单 / 备品备件
from . import gold_maintenance
# 法 (Method): SOP 作业指导书 / ECN 工程变更
from . import gold_sop_ecn
# 环 (Environment): 环境监测 / 危化品 / 能耗
from . import gold_environment
from . import gold_hazardous_chemical
from . import gold_energy

# ---- 生产后 (盘库 / 成品入库 / 班后回料) ----
from . import gold_inventory
from . import gold_finished_goods
from . import gold_material_return

# ---- 审计日志 (Phase 2) ----
from . import gold_audit_log

# 看板
from . import gold_dashboard
