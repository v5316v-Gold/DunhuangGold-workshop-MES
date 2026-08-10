# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 件级 SN(一物一码)
===================================

件级 SN = 个体首饰的唯一标识,贯穿:
  - 生产订单 → 工序报工 → 印记 → 质检 → NGTC 证书 → 销售 → 客户扫码

每件物品:
  - 全球唯一 SN (符合 GS1 / 内部规则)
  - 二维码 / RFID 编码
  - 关联生产订单、工序、印记、质检
  - 客户扫码可验证

SN 规则:
  - 内部编码: GLD-<YYYYMMDD>-<款式代码>-<序号>
  - 例: GLD-20260805-RING-OWP-001-0001
  - 二维码内容: https://verify.dunhuang-gold-mes.com/piece/SN
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


PIECE_STATE = [
    ("draft", "草稿"),
    ("in_process", "生产中"),
    ("finished", "已完工"),
    ("stored", "已入库"),
    ("sold", "已销售"),
    ("redeemed", "已以旧换新"),
    ("scrap", "报废"),
]


class GoldPiece(models.Model):
    _name = "gold.piece"
    _description = "件级 SN(一物一码)"
    _order = "sn"
    _rec_name = "sn"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    sn = fields.Char(
        string="件级 SN",
        required=True,
        readonly=True,
        index=True,
        help="全球唯一标识符",
    )
    name = fields.Char(
        string="款式名称",
        help="冗余字段,便于查询",
    )
    # 关联
    production_id = fields.Many2one(
        "mrp.production",
        string="生产订单",
        ondelete="set null",
    )
    product_id = fields.Many2one(
        "product.product",
        string="产品",
        required=True,
    )
    # 重量
    standard_weight_g = fields.Float(
        string="标准重量 (g)",
        digits=(18, 6),
    )
    actual_weight_g = fields.Float(
        string="实际重量 (g)",
        digits=(18, 6),
    )
    # 印记
    imprint_id = fields.Many2one(
        "gold.imprint",
        string="印记",
    )
    imprint_content = fields.Char(
        string="印记内容",
        related="imprint_id.imprint_content",
    )
    # 质检
    qc_id = fields.Many2one(
        "gold.quality.inspection",
        string="质检",
    )
    qc_passed = fields.Boolean(
        string="质检合格",
        related="qc_id.result",
    )
    # XRF
    xrf_id = fields.Many2one(
        "gold.xrf.record",
        string="XRF 检测",
    )
    # NGTC 证书
    ngtc_cert_no = fields.Char(
        string="NGTC 证书号",
    )
    ngtc_cert_image = fields.Binary(string="NGTC 证书")
    # 状态
    state = fields.Selection(
        PIECE_STATE,
        string="状态",
        default="draft",
        required=True,
        tracking=True,
    )
    # 二维码
    qr_payload = fields.Char(
        string="二维码内容",
        compute="_compute_qr_payload",
        store=True,
        help="扫码识别的内容",
    )
    qr_image = fields.Binary(
        string="二维码图片",
        help="PNG/JPEG 二维码",
    )
    # 销售
    sale_order_id = fields.Many2one(
        "sale.order",
        string="销售订单",
    )
    sale_date = fields.Datetime(string="销售时间")
    # 客户
    customer_id = fields.Many2one(
        "res.partner",
        string="客户",
    )
    # 复合
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        default=lambda self: self.env.company,
    )
    # 备注
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("sn_unique", "UNIQUE(sn, company_id)", "件级 SN 必须唯一"),
    ]

    @api.depends("sn")
    def _compute_qr_payload(self):
        for rec in self:
            if rec.sn:
                rec.qr_payload = f"https://verify.dunhuang-gold-mes.com/piece/{rec.sn}"

    @api.model
    def create(self, vals):
        if not vals.get("sn") and vals.get("production_id"):
            # 自动生成 SN
            production = self.env["mrp.production"].browse(vals["production_id"])
            product = production.product_id
            style_code = product.default_code or "X"
            today = fields.Date.context_today(self)
            seq = self.env["ir.sequence"].next_by_code("gold.piece.sn")
            vals["sn"] = f"GLD-{today.strftime('%Y%m%d')}-{style_code}-{seq}"
        return super().create(vals)

    def name_get(self):
        result = []
        for rec in self:
            display = f"[{rec.sn}] {(rec.name or rec.product_id.display_name or '')}"
            result.append((rec.id, display))
        return result

    def action_verify(self):
        """扫码验证(Odoo 端接口)"""
        for rec in self:
            rec.message_post(body=_("🔍 扫码验证 @ %s") % fields.Datetime.now())

    @api.model
    def verify_by_sn(self, sn):
        """扫码追溯:通过 SN 查所有信息"""
        rec = self.search([("sn", "=", sn)], limit=1)
        if not rec:
            return {"found": False, "msg": "SN 不存在"}
        return {
            "found": True,
            "sn": rec.sn,
            "product": rec.product_id.display_name,
            "production": rec.production_id.name if rec.production_id else None,
            "imprint": rec.imprint_content,
            "qc_passed": rec.qc_passed,
            "ngtc_cert_no": rec.ngtc_cert_no,
            "ngtc_cert_image": rec.ngtc_cert_image,
            "state": rec.state,
            "actual_weight_g": rec.actual_weight_g,
        }
