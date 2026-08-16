# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 设备维护 (机 / Machine)
=============================================

作业指导书「机」要素之「全生命周期维护」:
  - 维护工单: 预防性 (PM) / 纠正性 (CM) / 故障检修 (BM)
  - 备件台账: 库存 + 安全库存预警 + 供应商

模型:
  - gold.maintenance.order  设备维护工单
  - gold.spare.part         备品备件
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

MAINTENANCE_TYPE_SELECTION = [
    ("pm", "预防性维护 (PM)"),
    ("cm", "纠正性维护 (CM)"),
    ("bm", "故障检修 (BM)"),
]

MAINTENANCE_PRIORITY_SELECTION = [
    ("0", "低"),
    ("1", "中"),
    ("2", "高"),
    ("3", "紧急"),
]

MAINTENANCE_STATE_SELECTION = [
    ("draft", "草稿"),
    ("planned", "已计划"),
    ("in_progress", "进行中"),
    ("done", "已完成"),
    ("cancelled", "已取消"),
]


class GoldMaintenanceOrder(models.Model):
    _name = "gold.maintenance.order"
    _description = "设备维护工单"
    _order = "priority desc, planned_date asc"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="工单号",
        readonly=True,
        default=lambda self: _("新工单"),
    )
    equipment_id = fields.Many2one(
        "gold.equipment",
        string="设备",
        required=True,
        index=True,
        ondelete="restrict",
    )
    maintenance_type = fields.Selection(
        MAINTENANCE_TYPE_SELECTION,
        string="维护类型",
        required=True,
        default="pm",
    )
    priority = fields.Selection(
        MAINTENANCE_PRIORITY_SELECTION,
        string="优先级",
        default="1",
        required=True,
    )
    state = fields.Selection(
        MAINTENANCE_STATE_SELECTION,
        string="状态",
        default="draft",
        required=True,
        tracking=True,
    )
    assignee_id = fields.Many2one(
        "res.users",
        string="责任人",
    )
    planned_date = fields.Date(string="计划日期")
    start_time = fields.Datetime(string="开始时间")
    end_time = fields.Datetime(string="完成时间")
    duration_hours = fields.Float(
        string="耗时 (小时)",
        digits=(10, 2),
        compute="_compute_duration",
        store=True,
    )
    description = fields.Text(string="维护内容 / 故障描述")
    action_taken = fields.Text(string="处理措施")
    maintenance_cost = fields.Float(string="维护费用 (元)", digits=(16, 2), default=0.0)
    spare_part_ids = fields.Many2many(
        "gold.spare.part",
        string="使用备件",
    )
    down_before = fields.Boolean(string="维护前已停机", default=False)
    note = fields.Text(string="备注")

    @api.depends("start_time", "end_time")
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time and rec.end_time > rec.start_time:
                delta = rec.end_time - rec.start_time
                rec.duration_hours = delta.total_seconds() / 3600.0
            else:
                rec.duration_hours = 0.0

    @api.model
    def create(self, vals):
        if vals.get("name", _("新工单")) == _("新工单"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "gold.maintenance.order"
            ) or _("新工单")
        return super().create(vals)

    def action_plan(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("仅草稿状态可计划"))
            rec.state = "planned"

    def action_start(self):
        for rec in self:
            if rec.state not in ("planned", "draft"):
                raise UserError(_("仅草稿/已计划状态可开始"))
            rec.state = "in_progress"
            rec.start_time = rec.start_time or fields.Datetime.now()
            if rec.equipment_id.state in ("idle", "down"):
                rec.equipment_id.state = "maintenance"

    def action_done(self):
        for rec in self:
            if rec.state != "in_progress":
                raise UserError(_("仅进行中状态可完成"))
            rec.state = "done"
            rec.end_time = fields.Datetime.now()
            rec.equipment_id.state = "idle"

    def action_cancel(self):
        for rec in self:
            if rec.state == "done":
                raise UserError(_("已完成的工单不可取消"))
            rec.state = "cancelled"

    def name_get(self):
        result = []
        for rec in self:
            display = f"{rec.name} {rec.equipment_id.name or ''}"
            result.append((rec.id, display))
        return result


class GoldSparePart(models.Model):
    _name = "gold.spare.part"
    _description = "备品备件"
    _order = "code"
    _rec_name = "name"

    code = fields.Char(string="备件编号", required=True, size=32)
    name = fields.Char(string="备件名称", required=True)
    category = fields.Char(string="备件类别")
    equipment_ids = fields.Many2many(
        "gold.equipment",
        string="适用设备",
    )
    stock_qty = fields.Float(string="当前库存", digits=(16, 2), default=0.0)
    min_stock_qty = fields.Float(string="安全库存", digits=(16, 2), default=0.0)
    unit = fields.Char(string="单位", default="件")
    location = fields.Char(string="存放位置")
    supplier_id = fields.Many2one(
        "res.partner",
        string="供应商",
    )
    unit_price = fields.Float(string="参考单价 (元)", digits=(16, 2), default=0.0)
    is_low_stock = fields.Boolean(
        string="低库存",
        compute="_compute_low_stock",
        store=True,
    )
    active = fields.Boolean(string="启用", default=True)
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("spare_part_code_unique", "UNIQUE(code)", "备件编号必须唯一"),
        ("spare_part_stock_positive", "CHECK(stock_qty >= 0)", "库存必须 ≥ 0"),
    ]

    @api.depends("stock_qty", "min_stock_qty")
    def _compute_low_stock(self):
        for rec in self:
            rec.is_low_stock = rec.stock_qty < rec.min_stock_qty

    def name_get(self):
        result = []
        for rec in self:
            display = f"[{rec.code}] {rec.name}"
            result.append((rec.id, display))
        return result
