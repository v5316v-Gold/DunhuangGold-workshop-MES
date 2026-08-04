# -*- coding: utf-8 -*-
"""
贵金属车间 ERP — 工艺工序字典
==============================

工艺工序原子化,所有工序代码 + 名称 + 工艺归属 + 工时与损耗定额。
工序代码全局唯一,被工艺路线 / BOM / 报工单全套引用。

油压 9 道(code 前缀 OWP):
  OWP01 - 设计开模
  OWP02 - 备料
  OWP03 - 落料
  OWP04 - 油压成形
  OWP05 - 切边 / 修边
  OWP06 - 执模
  OWP07 - 抛光
  OWP08 - 印记
  OWP09 - 检验入库

失蜡 11 道(code 前缀 LWC):
  LWC01 - 设计
  LWC02 - 起版
  LWC03 - 雕蜡 / 3D 打印
  LWC04 - 树
  LWC05 - 灌石膏 / 脱蜡 / 焙烧
  LWC06 - 熔金浇铸
  LWC07 - 冲石膏 / 拆树
  LWC08 - 执模
  LWC09 - 镶石 (可选)
  LWC10 - 抛光
  LWC11 - 印记 / 检验入库

共用工序:
  COMMON_SORT - 分拣
  COMMON_QC - 专检
  COMMON_PACK - 包装
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


PROCESS_TYPE_SELECTION = [
    ("oil_press", "油压 (冲压)"),
    ("lost_wax", "失蜡铸造"),
    ("common", "共用"),
]


class GoldProcessOperation(models.Model):
    _name = "gold.process.operation"
    _description = "工艺工序字典"
    _order = "process_type, sequence, code"
    _rec_name = "name"

    code = fields.Char(
        string="工序代码",
        required=True,
        size=16,
        help="全局唯一,如 OWP04 / LWC06",
    )
    name = fields.Char(
        string="工序名称",
        required=True,
        translate=True,
    )
    process_type = fields.Selection(
        PROCESS_TYPE_SELECTION,
        string="工艺归属",
        required=True,
        default="common",
    )
    sequence = fields.Integer(
        string="顺序",
        default=10,
        help="在工艺路线中的展示顺序",
    )

    # 工艺定额
    standard_time_hours = fields.Float(
        string="标准工时 (小时/件)",
        digits=(10, 4),
        default=0.0,
        help="工序级工时定额,按件计",
    )
    standard_loss_rate = fields.Float(
        string="标准损耗率 (%)",
        digits=(6, 4),
        default=0.0,
        help="工序级损耗定额,占输入克重百分比,如 失蜡熔金 8.0 / 油压切边 1.5",
    )
    # 设备工位
    equipment_category = fields.Selection(
        [
            ("oil_press_machine", "油压机"),
            ("blanking_machine", "落料机"),
            ("trimming_machine", "切边机"),
            ("wax_carver", "雕蜡机"),
            ("sla_printer", "3D 打印机 (SLA/DLP)"),
            ("lost_wax_furnace", "失蜡炉"),
            ("centrifugal_caster", "离心铸造机"),
            ("vacuum_investor", "真空灌浆机"),
            ("burnout_furnace", "焙烧炉"),
            ("melting_furnace", "熔金炉"),
            ("laser_welder", "激光焊机"),
            ("laser_marker", "激光打字机"),
            ("polishing_machine", "抛光机"),
            ("magnetic_polisher", "磁力抛光机"),
            ("plating_tank", "电镀槽"),
            ("xrf", "XRF 含量检测"),
            ("balance", "电子天平"),
            ("bench", "工作台"),
            ("microscope", "显微镜"),
        ],
        string="设备类别",
    )
    workstation_id = fields.Many2one(
        "gold.workstation",
        string="默认工位",
        help="工序执行工位,可在工位维度改派",
    )
    # 检验
    need_quality_check = fields.Boolean(
        string="需要专检",
        default=False,
        help="是否需要质检员专检,影响工单流转",
    )
    # 数据采集
    collect_weight = fields.Boolean(
        string="采集重量",
        default=True,
        help="电子天平直采投料 / 产出重量",
    )
    collect_dimension = fields.Boolean(
        string="采集尺寸",
        default=False,
        help="三坐标 / 卡尺采集尺寸",
    )
    # 业务
    can_outsource = fields.Boolean(
        string="可外协",
        default=False,
        help="是否可外协加工(影响委外工单)",
    )
    returnable_wax = fields.Boolean(
        string="回收蜡",
        default=False,
        help="是否产生可回收蜡料,如失蜡",
    )
    returnable_gold = fields.Boolean(
        string="产生浇口回炉",
        default=False,
        help="失蜡熔金是否产生浇口回炉金料",
    )
    active = fields.Boolean(string="启用", default=True)
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "工序代码必须唯一"),
        (
            "loss_rate_range",
            "CHECK(standard_loss_rate >= 0 AND standard_loss_rate <= 100)",
            "损耗率必须在 0-100 之间",
        ),
    ]

    @api.constrains("standard_time_hours")
    def _check_time(self):
        for rec in self:
            if rec.standard_time_hours < 0:
                raise ValidationError(_("标准工时不能为负"))

    def name_get(self):
        """工序显示: [OWP04] 油压成形"""
        result = []
        for rec in self:
            display = f"[{rec.code}] {rec.name}"
            result.append((rec.id, display))
        return result
