# -*- coding: utf-8 -*-
"""
贵金属车间 ERP — 工艺路线模板
==============================

工艺路线模板 = 工序的有序集合 + 损耗定额 + 工时定额。
款式(产品)通过 mrp.routing 引用模板,生成生产订单时按工序展开生成工单。

路线模板是和款式解耦的预制件:
  - 油压标准 9 道
  - 失蜡标准 11 道
  - 失蜡(简)8 道  (省略树 / 拆树)
  - 失蜡(含镶石)11 道 (LWC09 启用)
  - 加急版 (省略抛光或压缩工时)

适用于:
  - 新款式:选择模板克隆路线
  - 工序调整:直接在模板上微调
  - 损耗追溯:从模板工序汇总
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


ROUTE_VARIANT_SELECTION = [
    ("standard", "标准"),
    ("simple", "精简"),
    ("express", "加急"),
    ("custom", "客户定制"),
]


class GoldProcessRoute(models.Model):
    _name = "gold.process.route"
    _description = "工艺路线模板"
    _order = "process_type, sequence, code"
    _rec_name = "name"

    code = fields.Char(
        string="路线编码",
        required=True,
        size=32,
        help="如 OWP_STD / LWC_STD / LWC_STD_INLAY",
    )
    name = fields.Char(
        string="路线名称",
        required=True,
        translate=True,
    )
    process_type = fields.Selection(
        [
            ("oil_press", "油压"),
            ("lost_wax", "失蜡"),
        ],
        string="工艺类型",
        required=True,
    )
    variant = fields.Selection(
        ROUTE_VARIANT_SELECTION,
        string="路线变体",
        default="standard",
        required=True,
    )
    sequence = fields.Integer(string="顺序", default=10)
    operation_ids = fields.One2many(
        "gold.process.route.line",
        "route_id",
        string="工序明细",
    )
    total_standard_time = fields.Float(
        string="合计标准工时 (小时)",
        compute="_compute_totals",
        store=True,
        digits=(10, 4),
    )
    total_loss_rate = fields.Float(
        string="合计损耗率 (%)",
        compute="_compute_totals",
        store=True,
        digits=(6, 4),
        help="叠加公式: 1 - Π(1 - li%)",
    )
    operation_count = fields.Integer(
        string="工序数",
        compute="_compute_totals",
        store=True,
    )
    active = fields.Boolean(string="启用", default=True)
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "路线编码必须唯一"),
    ]

    @api.depends("operation_ids.standard_time_hours", "operation_ids.standard_loss_rate")
    def _compute_totals(self):
        for route in self:
            total_time = 0.0
            total_loss_compound = 1.0
            for line in route.operation_ids:
                total_time += line.standard_time_hours
                # 损耗率叠加:总损耗 = 1 - Π(1 - li%)
                total_loss_compound *= (1 - line.standard_loss_rate / 100.0)
            route.total_standard_time = total_time
            route.total_loss_rate = (1 - total_loss_compound) * 100.0
            route.operation_count = len(route.operation_ids)

    @api.constrains("operation_ids")
    def _check_unique_sequence(self):
        for route in self:
            seqs = [l.sequence for l in route.operation_ids]
            if len(seqs) != len(set(seqs)):
                raise ValidationError(_("路线内工序顺序不能重复"))

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default.setdefault("code", _("%s (copy)") % self.code)
        default.setdefault("name", _("%s (副本)") % self.name)
        new_route = super().copy(default)
        # 复制明细
        for line in self.operation_ids:
            line.copy({"route_id": new_route.id})
        return new_route


class GoldProcessRouteLine(models.Model):
    _name = "gold.process.route.line"
    _description = "工艺路线明细"
    _order = "sequence, id"

    route_id = fields.Many2one(
        "gold.process.route",
        string="所属路线",
        required=True,
        ondelete="cascade",
    )
    operation_id = fields.Many2one(
        "gold.process.operation",
        string="工序",
        required=True,
    )
    sequence = fields.Integer(
        string="顺序",
        required=True,
        default=10,
    )
    process_type = fields.Selection(
        related="operation_id.process_type",
        string="工艺归属",
        store=True,
    )
    standard_time_hours = fields.Float(
        string="标准工时 (小时/件)",
        digits=(10, 4),
    )
    standard_loss_rate = fields.Float(
        string="标准损耗率 (%)",
        digits=(6, 4),
    )
    workstation_id = fields.Many2one(
        "gold.workstation",
        string="工位",
        help="覆盖工序的默认工位",
    )
    need_quality_check = fields.Boolean(
        string="需要专检",
        default=False,
    )
    is_optional = fields.Boolean(
        string="可选工序",
        default=False,
        help="如镶石,某些款式不启用",
    )
    note = fields.Char(string="备注")

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        if self.operation_id:
            self.standard_time_hours = self.operation_id.standard_time_hours
            self.standard_loss_rate = self.operation_id.standard_loss_rate
            self.need_quality_check = self.operation_id.need_quality_check
            self.workstation_id = self.operation_id.workstation_id
