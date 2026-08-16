# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 成品入库 (生产后)
========================================

成品入库 = 已完工的件级 SN (gold.piece) 扫码入库:
  - piece 状态 finished → stored (一物一码入库)
  - 汇总入库件数 / 总重量
  - 可选生成「成品批次」gold.material.batch(source=finished_goods)

模型:
  - gold.finished.goods       成品入库单(单头)
  - gold.finished.goods.line  入库明细(逐件 SN)
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

FINISHED_GOODS_STATE_SELECTION = [
    ("draft", "草稿"),
    ("posted", "已入库"),
    ("cancelled", "已取消"),
]


class GoldFinishedGoods(models.Model):
    _name = "gold.finished.goods"
    _description = "成品入库单"
    _order = "post_date desc, id desc"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="入库单号",
        readonly=True,
        default=lambda self: _("新入库"),
    )
    post_date = fields.Date(
        string="入库日期",
        default=fields.Date.context_today,
        required=True,
    )
    production_id = fields.Many2one(
        "mrp.production",
        string="生产订单",
    )
    location_id = fields.Many2one(
        "stock.location",
        string="成品库位",
    )
    line_ids = fields.One2many(
        "gold.finished.goods.line",
        "goods_id",
        string="入库明细",
    )
    generate_batch = fields.Boolean(
        string="生成成品批次",
        default=False,
        help="入库时同步生成金料成品批次(source=finished_goods)",
    )
    batch_id = fields.Many2one(
        "gold.material.batch",
        string="成品批次",
        readonly=True,
    )
    state = fields.Selection(
        FINISHED_GOODS_STATE_SELECTION,
        string="状态",
        default="draft",
        required=True,
        tracking=True,
    )
    total_piece_count = fields.Integer(
        string="入库件数",
        compute="_compute_totals",
        store=True,
    )
    total_weight_g = fields.Float(
        string="总重量 (g)",
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

    @api.depends("line_ids", "line_ids.actual_weight_g")
    def _compute_totals(self):
        for rec in self:
            rec.total_piece_count = len(rec.line_ids)
            rec.total_weight_g = sum(rec.line_ids.mapped("actual_weight_g") or [0.0])

    @api.model
    def create(self, vals):
        if vals.get("name", _("新入库")) == _("新入库"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "gold.finished.goods"
            ) or _("新入库")
        return super().create(vals)

    def action_post(self):
        """入库: 件级 SN 状态 → stored, 可选生成成品批次"""
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("仅草稿状态可入库"))
            if not rec.line_ids:
                raise UserError(_("入库明细为空"))
            pieces = rec.line_ids.mapped("piece_id")
            non_finished = pieces.filtered(lambda p: p.state != "finished")
            if non_finished:
                raise UserError(
                    _("以下件级 SN 未完工, 不可入库: %s")
                    % ", ".join(non_finished.mapped("sn"))
                )
            pieces.write({"state": "stored"})
            if rec.generate_batch:
                rec._create_batch()
            rec.state = "posted"

    def _create_batch(self):
        """为本次入库生成对应的金料批次(source=finished_goods)。

        修复点:
          1. 不再直接写 ``available_weight_g`` —— 它是 compute 字段,
             会按 ``net_weight_g - allocated - consumed`` 自动重算,
             直接 write 会被覆盖,造成账实不符。
          2. 不再 ``write({'state': 'available'})`` 绕过 action_available,
             改为正常路径,触发 inspection_state / net_weight_g 校验。
          3. ``batch_no`` 由 ``ir.sequence`` 自动分配,``name`` 仅做备注,
             不混用。
        """
        self.ensure_one()
        products = self.line_ids.mapped("piece_id.product_id")
        if len(products) != 1:
            raise UserError(_("成品批次要求入库明细为同一款物料, 多款式请拆单"))
        product = products
        batch = self.env["gold.material.batch"].create({
            "name": f"成品入库-{self.name}",  # 可选备注
            "product_id": product.id,
            "source": "finished_goods",
            "net_weight_g": self.total_weight_g,
            "gross_weight_g": self.total_weight_g,
            "inspection_state": "passed",
            "state": "draft",
        })
        # 走正常 action_available 路径,触发状态机 + 平衡校验
        batch.action_available()
        self.batch_id = batch.id
        return batch

    def action_cancel(self):
        for rec in self:
            if rec.state == "posted":
                raise UserError(_("已入库单据不可取消"))
            rec.state = "cancelled"

    def name_get(self):
        result = []
        for rec in self:
            display = f"{rec.name} ({rec.total_piece_count} 件)"
            result.append((rec.id, display))
        return result


class GoldFinishedGoodsLine(models.Model):
    _name = "gold.finished.goods.line"
    _description = "成品入库明细"
    _order = "id"
    _rec_name = "piece_id"

    goods_id = fields.Many2one(
        "gold.finished.goods",
        string="入库单",
        required=True,
        ondelete="cascade",
    )
    piece_id = fields.Many2one(
        "gold.piece",
        string="件级 SN",
        required=True,
        ondelete="restrict",
        domain="[('state', '=', 'finished')]",
    )
    product_id = fields.Many2one(
        "product.product",
        string="产品",
        related="piece_id.product_id",
    )
    actual_weight_g = fields.Float(
        string="实重 (g)",
        digits=(18, 6),
        default=0.0,
        help="默认取件级 SN 实际重量",
    )
    note = fields.Text(string="备注")

    @api.onchange("piece_id")
    def _onchange_piece(self):
        if self.piece_id:
            self.actual_weight_g = self.piece_id.actual_weight_g or 0.0

    def name_get(self):
        result = []
        for rec in self:
            display = f"{rec.piece_id.sn or ''} {rec.actual_weight_g:.3f}g"
            result.append((rec.id, display))
        return result
