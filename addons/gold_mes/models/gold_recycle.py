# -*- coding: utf-8 -*-
"""
贵金属车间 ERP — 旧金回收
==========================

旧金回收 = 客户来料 → 称重 → 化验 → 估价 → 提纯 → 入库

核心公式:
  回收额 = 实际重量 × 含量 × 当日金价 × 折价系数

合规:
  - 实名登记 + 身份证 OCR
  - ≥10000 触发报告
  - 增值税 / 消费税 / 个人所得税
  - 单据保存期 ≥ 5 年

数据流:
  1. 客户来料 → 实名 + 身份证
  2. 称重 (0.001g) → 录入
  3. XRF (初检) → 含量
  4. 火试 (抽检) → 终判
  5. 估价 → 客户确认
  6. 提纯 → 入库 (回收料批次)
  7. 税务 → 发票
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


RECYCLE_STATE_SELECTION = [
    ("draft", "草稿"),
    ("inspecting", "化验中"),
    ("quoted", "已报价"),
    ("confirmed", "客户确认"),
    ("refining", "提纯中"),
    ("done", "入库"),
    ("cancelled", "取消"),
]


class GoldRecycle(models.Model):
    _name = "gold.recycle"
    _description = "旧金回收单"
    _order = "name desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"

    name = fields.Char(
        string="回收单号",
        required=True,
        readonly=True,
        default=lambda self: _("新回收单"),
    )
    # 客户
    partner_id = fields.Many2one(
        "res.partner",
        string="客户",
        required=True,
    )
    id_number = fields.Char(
        string="身份证号",
        required=True,
        size=32,
    )
    id_image = fields.Binary(string="身份证照片")
    phone = fields.Char(string="联系电话")
    address = fields.Char(string="地址")
    # 物料
    categ_id = fields.Many2one(
        "product.category",
        string="物料分类",
        required=True,
        domain="[('gold_metal_type', 'in', ['fine_gold', 'k_gold', 'platinum', 'palladium', 'silver', 'recycle'])]",
    )
    # 重量 / 含量
    gross_weight_g = fields.Float(
        string="毛重 (g)",
        digits=(18, 6),
        required=True,
        default=0.0,
    )
    tare_weight_g = fields.Float(
        string="皮重 (g)",
        digits=(18, 6),
        default=0.0,
        help="容器 / 杂质扣除",
    )
    net_weight_g = fields.Float(
        string="净重 (g)",
        digits=(18, 6),
        required=True,
        default=0.0,
    )
    xrf_purity = fields.Float(
        string="XRF 含量 (%)",
        digits=(6, 4),
        default=0.0,
    )
    fire_purity = fields.Float(
        string="火试含量 (%)",
        digits=(6, 4),
        default=0.0,
        help="火试抽检,精度更高",
    )
    final_purity = fields.Float(
        string="最终含量 (%)",
        digits=(6, 4),
        compute="_compute_final_purity",
        store=True,
    )
    # 估价
    price_at_time = fields.Float(
        string="当时金价 (元/g)",
        digits=(18, 4),
        default=0.0,
    )
    discount_factor = fields.Float(
        string="折价系数",
        digits=(6, 4),
        default=0.97,
        help="回收料典型 0.95-0.98",
    )
    valuation_amount = fields.Float(
        string="回收金额 (元)",
        digits=(18, 2),
        compute="_compute_valuation",
        store=True,
    )
    # 检验
    inspector_id = fields.Many2one(
        "res.users",
        string="检验员",
    )
    inspection_date = fields.Datetime(string="化验时间")
    # 反洗钱
    is_large_amount = fields.Boolean(
        string="大额",
        compute="_compute_aml",
        store=True,
    )
    aml_report_id = fields.Char(
        string="AML 报告编号",
        help="大额 / 可疑交易报告编号",
    )
    # 状态
    state = fields.Selection(
        RECYCLE_STATE_SELECTION,
        string="状态",
        default="draft",
        required=True,
        tracking=True,
    )
    # 后续
    batch_id = fields.Many2one(
        "gold.material.batch",
        string="入库批次",
        readonly=True,
    )
    invoice_id = fields.Many2one(
        "account.move",
        string="发票",
    )
    note = fields.Text(string="备注")
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        ("net_weight_positive", "CHECK(net_weight_g > 0)", "净重必须 > 0"),
        ("purity_range", "CHECK(xrf_purity >= 0 AND xrf_purity <= 100)", "含量必须在 0-100"),
    ]

    @api.depends("xrf_purity", "fire_purity")
    def _compute_final_purity(self):
        for rec in self:
            if rec.fire_purity > 0:
                rec.final_purity = rec.fire_purity
            else:
                rec.final_purity = rec.xrf_purity

    @api.depends("net_weight_g", "final_purity", "price_at_time", "discount_factor")
    def _compute_valuation(self):
        for rec in self:
            # 换算到纯金重量 = 净重 × 含量
            pure_g = rec.net_weight_g * (rec.final_purity / 100.0)
            rec.valuation_amount = pure_g * rec.price_at_time * rec.discount_factor

    @api.depends("valuation_amount")
    def _compute_aml(self):
        for rec in self:
            rec.is_large_amount = rec.valuation_amount >= 50000.0  # ≥ 5万触发大额[推]

    @api.onchange("gross_weight_g", "tare_weight_g")
    def _onchange_net_weight(self):
        for rec in self:
            rec.net_weight_g = (rec.gross_weight_g or 0.0) - (rec.tare_weight_g or 0.0)

    @api.model
    def create(self, vals):
        if vals.get("name", _("新回收单")) == _("新回收单"):
            vals["name"] = self.env["ir.sequence"].next_by_code("gold.recycle")
        return super().create(vals)

    def action_inspecting(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("仅草稿可启动化验"))
            if rec.net_weight_g <= 0:
                raise UserError(_("净重必须 > 0"))
            if not rec.partner_id or not rec.id_number:
                raise UserError(_("客户实名信息不全"))
            rec.state = "inspecting"

    def action_quoted(self):
        for rec in self:
            if rec.state != "inspecting":
                raise UserError(_("仅化验中可报价"))
            if rec.final_purity <= 0:
                raise UserError(_("最终含量未确定"))
            if rec.price_at_time <= 0:
                raise UserError(_("金价未确定"))
            rec.state = "quoted"

    def action_confirmed(self):
        for rec in self:
            if rec.state != "quoted":
                raise UserError(_("仅已报价单可确认"))
            rec.state = "confirmed"

    def action_refining(self):
        for rec in self:
            if rec.state != "confirmed":
                raise UserError(_("仅客户确认后可提纯"))
            rec.state = "refining"

    def action_done(self):
        """提纯入库 → 生成回收料批次"""
        for rec in self:
            if rec.state != "refining":
                raise UserError(_("仅提纯中可入库"))
            if not rec.categ_id:
                raise UserError(_("物料分类未指定"))
            # 创建回收料批次
            product = self.env["product.product"].search(
                [
                    ("categ_id", "=", rec.categ_id.id),
                    ("gold_metal_type", "in", ["recycle", "fine_gold"]),
                ],
                limit=1,
            )
            if not product:
                # 找不到就用回收料分类物料
                product = self.env["product.product"].create({
                    "name": f"回收料-{rec.name}",
                    "categ_id": rec.categ_id.id,
                    "gold_metal_type": "recycle",
                    "gold_purity": rec.final_purity,
                    "type": "product",
                })
            batch = self.env["gold.material.batch"].create({
                "name": f"旧金回收-{rec.name}",
                "product_id": product.id,
                "source": "recycle",
                "recycle_order_id": rec.id,
                "net_weight_g": rec.net_weight_g,
                "gross_weight_g": rec.gross_weight_g,
                "available_weight_g": rec.net_weight_g,
                "discount_factor": rec.discount_factor,
                "is_recycle": True,
                "unit_price": rec.price_at_time * rec.discount_factor,
                "inspection_state": "passed",
                "inspector_id": rec.inspector_id.id,
                "inspection_date": rec.inspection_date or fields.Datetime.now(),
            })
            batch.write({"state": "available"})
            rec.batch_id = batch.id
            rec.state = "done"

    def action_cancel(self):
        for rec in self:
            if rec.state in ["done"]:
                raise UserError(_("已入库单据不可取消"))
            rec.state = "cancelled"

    def name_get(self):
        result = []
        for rec in self:
            display = f"[{rec.name}] {rec.partner_id.name} {rec.net_weight_g:.3f}g"
            result.append((rec.id, display))
        return result
