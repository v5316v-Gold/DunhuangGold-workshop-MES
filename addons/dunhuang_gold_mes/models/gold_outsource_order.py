# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 委外加工订单
==============================

外协场景:
  - 失蜡外协 (部分款式委外铸造)
  - 镶石外协 (高端镶嵌)
  - 电镀外协 (玫瑰金 / 镀铑)
  - 抛光外协 (粗抛或镜面)

核心管控:
  - 金料批次从金库出库 → 委外库
  - 委外加工 → 收料称重
  - 损耗分摊: 投料 - 收回 = 损耗
  - 结算: 加工费 + 金料损耗
  - 税务: 加工费发票(增值税 13%)

合规:
  - 包工包料 vs 包工不包料
  - 加工费发票要求
  - 反洗钱(连续大额外协)
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


OUTSOURCE_STATE = [
    ("draft", "草稿"),
    ("issued", "已发料"),
    ("processing", "加工中"),
    ("received", "已收回"),
    ("invoiced", "已结算"),
    ("closed", "已关闭"),
    ("cancelled", "取消"),
]


OUTSOURCE_TYPE = [
    ("include_material", "包工包料"),
    ("exclude_material", "包工不包料"),
]


OUTSOURCE_PROCESS = [
    ("lost_wax", "失蜡铸造"),
    ("stone_setting", "镶石"),
    ("plating", "电镀"),
    ("polishing", "抛光"),
    ("laser_weld", "激光焊接"),
    ("other", "其他"),
]


class GoldOutsourceOrder(models.Model):
    _name = "gold.outsource.order"
    _description = "委外加工订单"
    _order = "name desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"

    name = fields.Char(
        string="委外单号",
        required=True,
        readonly=True,
        default=lambda self: _("新委外"),
    )
    # 业务
    outsource_type = fields.Selection(
        OUTSOURCE_TYPE,
        string="业务类型",
        default="exclude_material",
        required=True,
        help="包工包料 = 加工方提供金料;包工不包料 = 我方提供金料",
    )
    process_type = fields.Selection(
        OUTSOURCE_PROCESS,
        string="加工工艺",
        required=True,
    )
    # 关联
    partner_id = fields.Many2one(
        "res.partner",
        string="外协厂",
        required=True,
        domain="[('is_company', '=', True)]",
    )
    production_id = fields.Many2one(
        "mrp.production",
        string="生产订单",
        required=True,
        ondelete="restrict",
    )
    operation_id = fields.Many2one(
        "gold.process.operation",
        string="工序",
        help="外协加工的工序,如 镶石 / 电镀",
    )
    # 物料
    outgoing_batch_id = fields.Many2one(
        "gold.material.batch",
        string="发料批次",
        required=True,
    )
    outgoing_weight_g = fields.Float(
        string="发料重量 (g)",
        digits=(18, 6),
        required=True,
    )
    # 收回
    incoming_weight_g = fields.Float(
        string="收回重量 (g)",
        digits=(18, 6),
        default=0.0,
    )
    incoming_piece_count = fields.Integer(
        string="收回件数",
        default=0,
    )
    incoming_batch_id = fields.Many2one(
        "gold.material.batch",
        string="收回批次",
        readonly=True,
    )
    # 损耗
    loss_g = fields.Float(
        string="损耗 (g)",
        digits=(18, 6),
        compute="_compute_loss",
        store=True,
    )
    loss_rate = fields.Float(
        string="损耗率 (%)",
        digits=(6, 4),
        compute="_compute_loss",
        store=True,
    )
    loss_charge_party = fields.Selection(
        [
            ("self", "我方承担"),
            ("supplier", "外协厂承担"),
        ],
        string="损耗承担方",
        default="supplier",
        required=True,
        help="通常外协超耗由外协厂承担",
    )
    # 结算
    processing_fee = fields.Float(
        string="加工费 (元)",
        digits=(16, 2),
        default=0.0,
    )
    gold_loss_charge = fields.Float(
        string="金料损耗佣金 (元)",
        digits=(16, 2),
        compute="_compute_charge",
        store=True,
    )
    total_amount = fields.Float(
        string="应付总额 (元)",
        digits=(16, 2),
        compute="_compute_charge",
        store=True,
    )
    invoice_id = fields.Many2one(
        "account.move",
        string="发票",
    )
    # 时间
    issue_date = fields.Date(
        string="发料日期",
        default=fields.Date.context_today,
    )
    expected_return_date = fields.Date(
        string="预计收回",
    )
    actual_return_date = fields.Date(
        string="实际收回",
    )
    # 状态
    state = fields.Selection(
        OUTSOURCE_STATE,
        string="状态",
        default="draft",
        required=True,
        tracking=True,
    )
    # 其他
    cert_no = fields.Char(string="外协检验证书")
    cert_image = fields.Binary(string="证书")
    note = fields.Text(string="备注")
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        (
            "outgoing_positive",
            "CHECK(outgoing_weight_g > 0)",
            "发料重量必须 > 0",
        ),
        (
            "incoming_positive",
            "CHECK(incoming_weight_g >= 0)",
            "收回重量必须 ≥ 0",
        ),
    ]

    @api.depends("outgoing_weight_g", "incoming_weight_g")
    def _compute_loss(self):
        for rec in self:
            rec.loss_g = max(0.0, rec.outgoing_weight_g - rec.incoming_weight_g)
            if rec.outgoing_weight_g > 0:
                rec.loss_rate = (rec.loss_g / rec.outgoing_weight_g) * 100
            else:
                rec.loss_rate = 0.0

    @api.depends("processing_fee", "gold_loss_charge", "loss_charge_party")
    def _compute_charge(self):
        for rec in self:
            # 金料损耗按当日金价 + 折价系数
            gold_price = rec.outgoing_batch_id.current_price or 0.0
            if rec.loss_charge_party == "supplier":
                # 外协承担损耗,只收加工费
                rec.gold_loss_charge = 0.0
            else:
                # 我方承担
                rec.gold_loss_charge = rec.loss_g * gold_price
            rec.total_amount = rec.processing_fee + rec.gold_loss_charge

    @api.model
    def create(self, vals):
        if vals.get("name", _("新委外")) == _("新委外"):
            vals["name"] = self.env["ir.sequence"].next_by_code("gold.outsource.order")
        return super().create(vals)

    def action_issue(self):
        """发料: 锁定批次 → 占用重量"""
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("仅草稿可发料"))
            if rec.outgoing_weight_g > rec.outgoing_batch_id.available_weight_g:
                raise UserError(
                    _("批次 %s 可用重量不足:申请 %.3fg,可用 %.3fg")
                    % (rec.outgoing_batch_id.batch_no, rec.outgoing_weight_g, rec.outgoing_batch_id.available_weight_g)
                )
            # 分配
            rec.outgoing_batch_id.allocate(rec.outgoing_weight_g)
            # 状态
            rec.state = "issued"
        return True

    def action_processing(self):
        for rec in self:
            if rec.state != "issued":
                raise UserError(_("仅已发料可启动加工"))
            rec.state = "processing"

    def action_receive(self, incoming_weight_g, piece_count):
        """收回: 减少批次已分配, 报工记录"""
        for rec in self:
            if rec.state not in ["issued", "processing"]:
                raise UserError(_("仅已发料 / 加工中可收回"))
            if incoming_weight_g <= 0:
                raise UserError(_("收回重量必须 > 0"))
            if piece_count <= 0:
                raise UserError(_("收回件数必须 > 0"))

            # 1. 释放批次已分配 + 消耗
            # 真正消耗 = 收回 + 损耗
            consumed = incoming_weight_g + rec.loss_g
            # 但实际流程是: 占用 out_weight_g → 收回 in_weight_g → 释放 (out - in)
            # 损耗被外协承担: out_weight_g 直接消耗, in_weight_g 进入新批次
            if rec.outgoing_batch_id.allocated_weight_g < rec.outgoing_weight_g:
                raise UserError(_("批次 %s 分配不足") % rec.outgoing_batch_id.batch_no)
            # 释放分配的剩余
            rec.outgoing_batch_id.release(rec.outgoing_weight_g)
            # 全部消耗
            rec.outgoing_batch_id.consume(rec.outgoing_weight_g)

            rec.incoming_weight_g = incoming_weight_g
            rec.incoming_piece_count = piece_count
            rec.actual_return_date = fields.Date.context_today(self)
            rec.state = "received"
        return True

    def action_invoice(self):
        for rec in self:
            if rec.state != "received":
                raise UserError(_("仅已收回可结算"))
            if rec.processing_fee <= 0 and rec.total_amount <= 0:
                raise UserError(_("加工费 / 应付金额必须 > 0"))
            rec.state = "invoiced"

    def action_close(self):
        for rec in self:
            if rec.state not in ["received", "invoiced"]:
                raise UserError(_("仅已收回 / 已结算可关闭"))
            rec.state = "closed"

    def action_cancel(self):
        for rec in self:
            if rec.state in ["closed"]:
                raise UserError(_("已关闭不可取消"))
            # 释放批次
            if rec.state == "issued":
                rec.outgoing_batch_id.release(rec.outgoing_weight_g)
            rec.state = "cancelled"

    def name_get(self):
        result = []
        for rec in self:
            display = f"[{rec.name}] {rec.partner_id.name} {rec.process_type} {rec.outgoing_weight_g:.3f}g"
            result.append((rec.id, display))
        return result
