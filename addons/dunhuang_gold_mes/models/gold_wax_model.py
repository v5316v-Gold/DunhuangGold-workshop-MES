# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 蜡模管理(失蜡专属)
====================================

蜡模 = 雕蜡 / 3D 打印 / 银版翻橡胶模
状态: 库存 / 已组树 / 浇铸完成 / 报废
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


WAX_STATE_SELECTION = [
    ("draft", "草稿"),
    ("stock", "库存"),
    ("in_tree", "已组树"),
    ("casted", "已浇铸"),
    ("scrapped", "报废"),
]


WAX_ORIGIN_SELECTION = [
    ("hand_carved", "手工雕蜡"),
    ("sla_print", "3D 打印 (SLA)"),
    ("dlp_print", "3D 打印 (DLP)"),
    ("rubber_mold", "橡胶模翻制"),
    ("silver_master", "银版翻制"),
]


class GoldWaxModel(models.Model):
    _name = "gold.wax.model"
    _description = "失蜡蜡模"
    _order = "code"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    code = fields.Char(
        string="蜡模编号",
        required=True,
        readonly=True,
        default=lambda self: _("新蜡模"),
    )
    name = fields.Char(
        string="蜡模名称",
        required=True,
    )
    style_id = fields.Many2one(
        "product.product",
        string="对应款式",
    )
    origin = fields.Selection(
        WAX_ORIGIN_SELECTION,
        string="来源",
        default="hand_carved",
        required=True,
    )
    # 重量
    weight_g = fields.Float(
        string="蜡模重量 (g)",
        digits=(18, 6),
        default=0.0,
    )
    # 状态
    state = fields.Selection(
        WAX_STATE_SELECTION,
        string="状态",
        default="draft",
        required=True,
        tracking=True,
    )
    # 关联
    cast_production_id = fields.Many2one(
        "mrp.production",
        string="浇铸工单",
        help="此蜡模参与的浇铸工单",
    )
    # 工艺
    sla_layer_thickness_um = fields.Float(
        string="SLA 层厚 (μm)",
        digits=(8, 2),
    )
    sla_exposure_sec = fields.Float(
        string="SLA 曝光 (秒)",
        digits=(8, 2),
    )
    sla_machine_id = fields.Many2one(
        "gold.equipment",
        string="3D 打印机",
    )
    active = fields.Boolean(string="启用", default=True)
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "蜡模编号必须唯一"),
    ]

    @api.model
    def create(self, vals):
        if vals.get("code", _("新蜡模")) == _("新蜡模"):
            vals["code"] = self.env["ir.sequence"].next_by_code("gold.wax.model")
        return super().create(vals)

    def action_stock(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("仅草稿可入库"))
            rec.state = "stock"

    def action_to_tree(self):
        for rec in self:
            if rec.state != "stock":
                raise UserError(_("仅库存蜡模可组树"))
            rec.state = "in_tree"

    def action_casted(self):
        for rec in self:
            if rec.state != "in_tree":
                raise UserError(_("仅已组树可浇铸"))
            rec.state = "casted"

    def action_scrap(self):
        for rec in self:
            rec.state = "scrapped"

    def name_get(self):
        result = []
        for rec in self:
            display = f"[{rec.code}] {rec.name}"
            result.append((rec.id, display))
        return result
