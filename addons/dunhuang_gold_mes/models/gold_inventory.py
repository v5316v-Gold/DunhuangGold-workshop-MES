# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 金料盘点 (生产后)
========================================

盘点单 = 盘点范围 + 明细(批次 × 账面 vs 实盘) + 复核审批 + 差异回写。

业务规则:
  - 盘点开始锁定涉及批次(state → locked), 防止盘点期间变动
  - 账面重量 = 批次净重; 实盘重量由电子天平录入
  - 差异 = 实盘 - 账面(盘盈为正, 盘亏为负)
  - 过账: 差异自动回写批次净重与可用重量(盘亏超过可用则拦截)
  - 复核人必须与盘点人不同(职责分离)

模型:
  - gold.inventory.count       金料盘点单(单头)
  - gold.inventory.count.line  盘点明细行
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

INVENTORY_STATE_SELECTION = [
    ("draft", "草稿"),
    ("counting", "盘点中"),
    ("reviewed", "已复核"),
    ("posted", "已过账"),
    ("cancelled", "已取消"),
]


class GoldInventoryCount(models.Model):
    _name = "gold.inventory.count"
    _description = "金料盘点单"
    _order = "inventory_date desc, id desc"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="盘点单号",
        readonly=True,
        default=lambda self: _("新盘点"),
    )
    inventory_date = fields.Date(
        string="盘点日期",
        default=fields.Date.context_today,
        required=True,
    )
    location_id = fields.Many2one(
        "stock.location",
        string="盘点库位",
        help="金库 / 半成品库 / 不良品库",
    )
    scope_note = fields.Char(string="盘点范围说明")
    counter_id = fields.Many2one(
        "res.users",
        string="盘点人",
        default=lambda self: self.env.user,
        required=True,
    )
    reviewer_id = fields.Many2one(
        "res.users",
        string="复核人",
        help="复核人必须与盘点人不同",
    )
    state = fields.Selection(
        INVENTORY_STATE_SELECTION,
        string="状态",
        default="draft",
        required=True,
        tracking=True,
    )
    line_ids = fields.One2many(
        "gold.inventory.count.line",
        "count_id",
        string="盘点明细",
    )
    # 汇总
    total_book_weight_g = fields.Float(
        string="账面合计 (g)",
        digits=(18, 6),
        compute="_compute_totals",
        store=True,
    )
    total_actual_weight_g = fields.Float(
        string="实盘合计 (g)",
        digits=(18, 6),
        compute="_compute_totals",
        store=True,
    )
    total_diff_g = fields.Float(
        string="差异合计 (g)",
        digits=(18, 6),
        compute="_compute_totals",
        store=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        default=lambda self: self.env.company,
    )
    note = fields.Text(string="备注")

    @api.depends(
        "line_ids",
        "line_ids.book_weight_g",
        "line_ids.actual_weight_g",
        "line_ids.diff_g",
    )
    def _compute_totals(self):
        for rec in self:
            rec.total_book_weight_g = sum(rec.line_ids.mapped("book_weight_g") or [0.0])
            rec.total_actual_weight_g = sum(rec.line_ids.mapped("actual_weight_g") or [0.0])
            rec.total_diff_g = sum(rec.line_ids.mapped("diff_g") or [0.0])

    @api.model
    def create(self, vals):
        if vals.get("name", _("新盘点")) == _("新盘点"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "gold.inventory.count"
            ) or _("新盘点")
        return super().create(vals)

    def action_start(self):
        """开始盘点: 锁定涉及批次"""
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("仅草稿状态可开始盘点"))
            if not rec.line_ids:
                raise UserError(_("盘点明细为空, 无法开始"))
            rec.line_ids.mapped("batch_id").action_lock()
            rec.state = "counting"

    def action_review(self):
        """复核"""
        for rec in self:
            if rec.state != "counting":
                raise UserError(_("仅盘点中状态可复核"))
            if not rec.reviewer_id:
                raise UserError(_("请指定复核人"))
            if rec.reviewer_id == rec.counter_id:
                raise UserError(_("复核人必须与盘点人不同 (职责分离)"))
            rec.state = "reviewed"

    def action_post(self):
        """过账: 差异回写批次并解锁"""
        for rec in self:
            if rec.state != "reviewed":
                raise UserError(_("仅已复核状态可过账"))
            for line in rec.line_ids:
                if abs(line.diff_g) > 0.0005:
                    line.batch_id.adjust(line.diff_g)
            rec.line_ids.mapped("batch_id").action_unlock()
            rec.state = "posted"

    def action_cancel(self):
        for rec in self:
            if rec.state == "posted":
                raise UserError(_("已过账的盘点单不可取消"))
            if rec.state == "counting":
                rec.line_ids.mapped("batch_id").action_unlock()
            rec.state = "cancelled"

    def name_get(self):
        result = []
        for rec in self:
            display = f"{rec.name} ({rec.inventory_date})"
            result.append((rec.id, display))
        return result


class GoldInventoryCountLine(models.Model):
    _name = "gold.inventory.count.line"
    _description = "金料盘点明细"
    _order = "batch_id"
    _rec_name = "batch_id"

    count_id = fields.Many2one(
        "gold.inventory.count",
        string="盘点单",
        required=True,
        ondelete="cascade",
    )
    batch_id = fields.Many2one(
        "gold.material.batch",
        string="金料批次",
        required=True,
        ondelete="restrict",
        domain="[('state', 'in', ['available', 'locked'])]",
    )
    book_weight_g = fields.Float(
        string="账面重量 (g)",
        digits=(18, 6),
        default=0.0,
        help="盘点开始时批次净重快照",
    )
    actual_weight_g = fields.Float(
        string="实盘重量 (g)",
        digits=(18, 6),
        default=0.0,
    )
    diff_g = fields.Float(
        string="盘盈亏 (g)",
        digits=(18, 6),
        compute="_compute_diff",
        store=True,
        help="实盘 - 账面, 正为盘盈, 负为盘亏",
    )
    note = fields.Text(string="备注")

    @api.depends("actual_weight_g", "book_weight_g")
    def _compute_diff(self):
        for rec in self:
            rec.diff_g = (rec.actual_weight_g or 0.0) - (rec.book_weight_g or 0.0)

    @api.onchange("batch_id")
    def _onchange_batch(self):
        if self.batch_id:
            self.book_weight_g = self.batch_id.net_weight_g

    def name_get(self):
        result = []
        for rec in self:
            display = f"{rec.batch_id.batch_no or ''} 账面{rec.book_weight_g:.3f}g/实盘{rec.actual_weight_g:.3f}g"
            result.append((rec.id, display))
        return result
