# -*- coding: utf-8 -*-
"""
贵金属车间 ERP — XRF 检测记录
==============================

依据 GB/T 18043-2013《首饰 贵金属含量的无损检测 X 射线荧光光谱法》

每件 (或每批抽样) 通过 XRF 检测,记录:
  - 检测编号
  - 物料 / 批次 / 订单
  - 测量人员
  - 测量结果: Au / Pt / Pd / Ag / Cu / Zn 含量(%)
  - 谱图 (附件)
  - 检测员电子签名
  - 判定是否符合注入 GB 11887-2012 标准
"""

from odoo import models, fields, api, _


class GoldXrfRecord(models.Model):
    _name = "gold.xrf.record"
    _description = "XRF 含量检测"
    _order = "detection_time desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"

    name = fields.Char(
        string="检测编号",
        required=True,
        readonly=True,
        default=lambda self: _("新检测"),
    )
    # 关联
    production_id = fields.Many2one(
        "mrp.production",
        string="生产订单",
    )
    product_id = fields.Many2one(
        "product.product",
        string="物料",
    )
    batch_id = fields.Many2one(
        "gold.material.batch",
        string="金料批次",
    )
    # 测量
    equipment_id = fields.Many2one(
        "gold.equipment",
        string="XRF 设备",
        domain=[("category", "=", "xrf")],
    )
    detection_time = fields.Datetime(
        string="检测时间",
        default=fields.Datetime.now,
    )
    # 人员
    operator_id = fields.Many2one(
        "res.users",
        string="检测员",
        required=True,
    )
    approver_id = fields.Many2one(
        "res.users",
        string="复核员",
    )
    # 含量结果
    gold_pct = fields.Float(
        string="Au 含量 (%)",
        digits=(6, 4),
    )
    platinum_pct = fields.Float(
        string="Pt 含量 (%)",
        digits=(6, 4),
    )
    palladium_pct = fields.Float(
        string="Pd 含量 (%)",
        digits=(6, 4),
    )
    silver_pct = fields.Float(
        string="Ag 含量 (%)",
        digits=(6, 4),
    )
    copper_pct = fields.Float(
        string="Cu 含量 (%)",
        digits=(6, 4),
    )
    zinc_pct = fields.Float(
        string="Zn 含量 (%)",
        digits=(6, 4),
    )
    nickel_pct = fields.Float(
        string="Ni 含量 (%)",
        digits=(6, 4),
    )
    # 综合
    main_metal_pct = fields.Float(
        string="主金属含量 (%)",
        digits=(6, 4),
        compute="_compute_main_metal",
        store=True,
        help="Au / Pt / Pd / Ag 中最高的含量",
    )
    standard_pct = fields.Float(
        string="标准下限 (%)",
        digits=(6, 4),
        default=99.00,
    )
    is_passed = fields.Boolean(
        string="是否合格",
        compute="_compute_passed",
        store=True,
    )
    # 谱图
    spectrum_image = fields.Binary(
        string="XRF 谱图",
    )
    spectrum_filename = fields.Char(string="谱图文件名")
    # 备注
    method = fields.Selection(
        [
            ("standard", "XRF 标准法"),
            ("quant", "XRF 定量法"),
            ("qualitative", "XRF 定性"),
        ],
        string="检测方法",
        default="standard",
    )
    duration_seconds = fields.Float(string="检测时长 (秒)")
    note = fields.Text(string="备注")

    @api.depends("gold_pct", "platinum_pct", "palladium_pct", "silver_pct")
    def _compute_main_metal(self):
        for rec in self:
            rec.main_metal_pct = max(
                rec.gold_pct,
                rec.platinum_pct,
                rec.palladium_pct,
                rec.silver_pct,
            )

    @api.depends("main_metal_pct", "standard_pct")
    def _compute_passed(self):
        for rec in self:
            rec.is_passed = rec.main_metal_pct >= rec.standard_pct

    @api.model
    def create(self, vals):
        if vals.get("name", _("新检测")) == _("新检测"):
            vals["name"] = self.env["ir.sequence"].next_by_code("gold.xrf.record")
        return super().create(vals)
