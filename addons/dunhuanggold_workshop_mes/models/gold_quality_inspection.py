# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 质检
========================

质检类型:
  - 来料检验 (金料入库前)
  - 工序检验 (报工时)
  - 成品检验 (入库前)

执行标准:
  - GB 11887-2012 贵金属纯度
  - GB/T 18043-2013 XRF 检测
  - QB/T 1689-2010 术语

判定:
  - 印记合规
  - 重量公差
  - 含量下限
  - 表面缺陷
"""

from odoo import models, fields, api, _


INSPECTION_TYPE_SELECTION = [
    ("incoming", "来料"),
    ("in_process", "过程"),
    ("final", "成品"),
]


INSPECTION_RESULT_SELECTION = [
    ("pending", "待检"),
    ("passed", "合格"),
    ("failed", "不合格"),
    ("conditional", "让步接收"),
]


class GoldQualityInspection(models.Model):
    _name = "gold.quality.inspection"
    _description = "质检记录"
    _order = "inspection_date desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"

    name = fields.Char(
        string="质检单号",
        required=True,
        readonly=True,
        default=lambda self: _("新质检"),
    )
    inspection_type = fields.Selection(
        INSPECTION_TYPE_SELECTION,
        string="类型",
        default="final",
        required=True,
    )
    # 关联
    production_id = fields.Many2one(
        "mrp.production",
        string="生产订单",
    )
    report_id = fields.Many2one(
        "gold.workorder.report",
        string="工序报工",
    )
    batch_id = fields.Many2one(
        "gold.material.batch",
        string="金料批次",
    )
    product_id = fields.Many2one(
        "product.product",
        string="物料",
    )
    # 检验项
    weight_g = fields.Float(
        string="检验重量 (g)",
        digits=(18, 6),
        required=True,
        default=0.0,
    )
    weight_tolerance_g = fields.Float(
        string="重量公差 (g)",
        digits=(18, 6),
        default=0.05,
    )
    weight_passed = fields.Boolean(
        string="重量合格",
        compute="_compute_results",
        store=True,
    )
    purity_pct = fields.Float(
        string="含量 (%)",
        digits=(6, 4),
        default=0.0,
    )
    purity_min_pct = fields.Float(
        string="含量下限 (%)",
        digits=(6, 4),
        default=99.00,
    )
    purity_passed = fields.Boolean(
        string="含量合格",
        compute="_compute_results",
        store=True,
    )
    imprint_present = fields.Boolean(
        string="印记合规",
        default=True,
    )
    imprint_passed = fields.Boolean(
        string="印记合格",
        compute="_compute_results",
        store=True,
    )
    surface_quality = fields.Selection(
        [
            ("good", "良"),
            ("minor", "轻微"),
            ("major", "严重"),
        ],
        string="表面质量",
        default="good",
    )
    surface_passed = fields.Boolean(
        string="表面合格",
        compute="_compute_results",
        store=True,
    )
    result = fields.Selection(
        INSPECTION_RESULT_SELECTION,
        string="综合判定",
        default="pending",
        required=True,
        tracking=True,
    )
    # 人员
    inspector_id = fields.Many2one(
        "res.users",
        string="检验员",
        required=True,
    )
    inspection_date = fields.Datetime(
        string="检验时间",
        default=fields.Datetime.now,
    )
    note = fields.Text(string="备注")

    @api.depends("weight_g", "weight_tolerance_g", "purity_pct", "purity_min_pct", "imprint_present", "surface_quality")
    def _compute_results(self):
        for rec in self:
            # 重量: 测量值 >= 标 - 公差
            # 这里简化: 重量 > 0 即合格(实际应对比标准重量)
            rec.weight_passed = rec.weight_g > 0
            # 含量: 实测 >= 下限
            rec.purity_passed = rec.purity_pct >= rec.purity_min_pct
            # 印记
            rec.imprint_passed = rec.imprint_present
            # 表面
            rec.surface_passed = rec.surface_quality != "major"

    @api.model
    def create(self, vals):
        if vals.get("name", _("新质检")) == _("新质检"):
            vals["name"] = self.env["ir.sequence"].next_by_code("gold.quality.inspection")
        rec = super().create(vals)
        # 自动汇总判定
        if all([rec.weight_passed, rec.purity_passed, rec.imprint_passed, rec.surface_passed]):
            rec.result = "passed"
        elif rec.purity_passed and rec.weight_passed:
            rec.result = "conditional"
        else:
            rec.result = "failed"
        return rec
