# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 班后回料 (生产后)
========================================

班后回料 = 工序剩余金料 / 蜡料退回金库:
  - 浇口料 / 边角料 / 抛光粉 / 返工废料 / 扫地金
  - 新建回料批次(source=return) 或 回入现有批次(调用 batch.receive)
  - 可关联报工单, 同步回收重量

模型:
  - gold.material.return  班后回料单
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

RETURN_STATE_SELECTION = [
    ("draft", "草稿"),
    ("confirmed", "已回库"),
    ("cancelled", "已取消"),
]

RETURN_SOURCE_SELECTION = [
    ("gate", "浇口料"),
    ("scrap_edge", "边角料"),
    ("polish_powder", "抛光粉"),
    ("rework_scrap", "返工废料"),
    ("sweep", "扫地金 / 杂料"),
    ("other", "其他"),
]

MATERIAL_TYPE_SELECTION = [
    ("gold", "金料"),
    ("wax", "蜡料"),
]


class GoldMaterialReturn(models.Model):
    _name = "gold.material.return"
    _description = "班后回料单"
    _order = "return_date desc, id desc"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="回料单号",
        readonly=True,
        default=lambda self: _("新回料"),
    )
    return_date = fields.Date(
        string="回料日期",
        default=fields.Date.context_today,
        required=True,
    )
    # 关联
    production_id = fields.Many2one(
        "mrp.production",
        string="生产订单",
    )
    workorder_id = fields.Many2one(
        "mrp.workorder",
        string="工单",
    )
    report_id = fields.Many2one(
        "gold.workorder.report",
        string="关联报工",
        help="回料可关联到具体工序报工",
    )
    workstation_id = fields.Many2one(
        "gold.workstation",
        string="回料工位",
    )
    operator_id = fields.Many2one(
        "res.users",
        string="操作员",
        default=lambda self: self.env.user,
        required=True,
    )
    # 回料属性
    return_source = fields.Selection(
        RETURN_SOURCE_SELECTION,
        string="回料来源",
        default="gate",
        required=True,
    )
    material_type = fields.Selection(
        MATERIAL_TYPE_SELECTION,
        string="物料类型",
        default="gold",
        required=True,
    )
    product_id = fields.Many2one(
        "product.product",
        string="金料物料",
        required=True,
        domain="[('categ_id.gold_metal_type', '!=', '')]",
        help="回料对应金料成色的物料",
    )
    weight_g = fields.Float(
        string="回料重量 (g)",
        digits=(18, 6),
        required=True,
        default=0.0,
    )
    # 目标批次
    create_new_batch = fields.Boolean(
        string="新建回料批次",
        default=True,
        help="勾选则新建批次; 不勾选则回入指定现有批次",
    )
    target_batch_id = fields.Many2one(
        "gold.material.batch",
        string="回入现有批次",
        domain="[('state', 'in', ['available', 'locked'])]",
    )
    batch_id = fields.Many2one(
        "gold.material.batch",
        string="回料批次",
        readonly=True,
        help="新建或回入的批次",
    )
    state = fields.Selection(
        RETURN_STATE_SELECTION,
        string="状态",
        default="draft",
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        default=lambda self: self.env.company,
    )
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("return_weight_positive", "CHECK(weight_g > 0)", "回料重量必须 > 0"),
    ]

    @api.model
    def create(self, vals):
        if vals.get("name", _("新回料")) == _("新回料"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "gold.material.return"
            ) or _("新回料")
        return super().create(vals)

    def action_confirm(self):
        """回库: 新建批次或回入现有批次"""
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("仅草稿状态可回库"))
            if rec.weight_g <= 0:
                raise UserError(_("回料重量必须 > 0"))
            if rec.create_new_batch:
                batch = self.env["gold.material.batch"].create({
                    "name": f"班后回料-{rec.name}",
                    "product_id": rec.product_id.id,
                    "source": "return",
                    "net_weight_g": rec.weight_g,
                    "gross_weight_g": rec.weight_g,
                    "available_weight_g": rec.weight_g,
                    "inspection_state": "passed",
                })
                batch.write({"state": "available"})
                rec.batch_id = batch.id
            else:
                if not rec.target_batch_id:
                    raise UserError(_("未勾选新建批次时, 必须指定回入的现有批次"))
                rec.target_batch_id.receive(rec.weight_g)
                rec.batch_id = rec.target_batch_id.id
            # 同步报工回收重量(金料)
            if rec.report_id and rec.material_type == "gold":
                rec.report_id.recyclable_gold_g += rec.weight_g
            rec.state = "confirmed"

    def action_cancel(self):
        for rec in self:
            if rec.state == "confirmed":
                raise UserError(_("已回库单据不可取消"))
            rec.state = "cancelled"

    def name_get(self):
        result = []
        for rec in self:
            display = f"{rec.name} {rec.product_id.name or ''} {rec.weight_g:.3f}g"
            result.append((rec.id, display))
        return result
