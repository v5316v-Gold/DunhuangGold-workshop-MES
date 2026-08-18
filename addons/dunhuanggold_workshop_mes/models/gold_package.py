# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 包装 (Phase 3.3)
====================================

成品质检通过后,车间打包:
  1. 按款/客户/订单分组装盒
  2. 盒贴 NGTC 防伪码(可扫码验真)
  3. 装箱(大件)
  4. 入库前最后一道关

数据模型:
  gold.package      包装盒
  gold.package.line 盒内件级 SN 明细

包装级别:
  - 盒 (box)   1+ 件 同款首饰
  - 箱 (case)  1+ 盒  多盒组合
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


PACKAGE_KIND = [
    ("box", "盒"),
    ("case", "箱"),
    ("pallet", "托盘"),
]

PACKAGE_STATE = [
    ("draft", "草稿"),
    ("sealed", "已封箱"),
    ("stored", "已入库"),
    ("shipped", "已发货"),
    ("opened", "已拆封"),  # 退货/换货
]


class GoldPackage(models.Model):
    _name = "gold.package"
    _description = "成品质检包装"
    _order = "package_time desc, id desc"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="包装号", required=True, readonly=True, default=lambda self: _("新包装"))
    package_no = fields.Char(string="包装条码", help="盒/箱外贴的条码", index=True)
    package_kind = fields.Selection(PACKAGE_KIND, string="包装类型", default="box", required=True)
    package_time = fields.Datetime(string="包装时间", default=fields.Datetime.now, required=True)
    # 关联
    production_id = fields.Many2one("mrp.production", string="生产订单", index=True)
    customer_id = fields.Many2one("res.partner", string="客户")
    line_ids = fields.One2many("gold.package.line", "package_id", string="盒内明细")
    piece_count = fields.Integer(string="件数", compute="_compute_counts", store=True)
    total_weight_g = fields.Float(string="总重量 (g)", digits=(18, 6), compute="_compute_counts", store=True)
    total_value = fields.Float(string="总价值 (元)", digits=(18, 2), compute="_compute_counts", store=True)
    # NGTC 证书
    ngtc_cert_no = fields.Char(string="NGTC 证书号")
    ngtc_cert_image = fields.Binary(string="NGTC 证书图片")
    # 防伪
    qr_payload = fields.Char(string="防伪二维码", compute="_compute_qr", store=True)
    qr_image = fields.Binary(string="防伪二维码图片")
    # 状态
    state = fields.Selection(PACKAGE_STATE, string="状态", default="draft", tracking=True, required=True)
    # 人员
    packager_id = fields.Many2one("res.users", string="包装人", default=lambda self: self.env.user)
    sealed_by_id = fields.Many2one("res.users", string="封箱人")
    sealed_time = fields.Datetime(string="封箱时间")
    # 公司
    company_id = fields.Many2one("res.company", string="公司", default=lambda self: self.env.company)
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("name_unique", "UNIQUE(name, company_id)", "包装号必须唯一"),
    ]

    @api.model
    def create(self, vals):
        if vals.get("name", _("新包装")) == _("新包装"):
            vals["name"] = self.env["ir.sequence"].next_by_code("gold.package") or _("新包装")
        if not vals.get("package_no"):
            vals["package_no"] = vals["name"]
        return super().create(vals)

    @api.depends("line_ids", "line_ids.piece_id")
    def _compute_counts(self):
        for rec in self:
            rec.piece_count = len(rec.line_ids)
            rec.total_weight_g = sum(rec.line_ids.mapped("actual_weight_g"))
            # 总价值 = 重量 × 锁价
            if rec.production_id and rec.production_id.gold_locked_price:
                rec.total_value = rec.total_weight_g * rec.production_id.gold_locked_price
            else:
                rec.total_value = 0.0

    @api.depends("name", "ngtc_cert_no")
    def _compute_qr(self):
        for rec in self:
            base = f"https://verify.dunhuang-gold-mes.com/package/{rec.name}"
            if rec.ngtc_cert_no:
                base += f"?ngtc={rec.ngtc_cert_no}"
            rec.qr_payload = base

    # 动作
    def action_seal(self):
        """封箱"""
        for rec in self:
            if not rec.line_ids:
                raise UserError(_("空包装不能封箱"))
            if rec.state != "draft":
                raise UserError(_("仅草稿状态可封箱 (当前: %s)") % rec.state)
            rec.write({
                "state": "sealed",
                "sealed_time": fields.Datetime.now(),
                "sealed_by_id": self.env.user.id,
            })
            # 标记件状态为 packaged
            for line in rec.line_ids:
                if line.piece_id:
                    line.piece_id.write({"state": "packaged"})

    def action_store(self):
        """入库"""
        for rec in self:
            if rec.state != "sealed":
                raise UserError(_("仅已封箱可入库 (当前: %s)") % rec.state)
            rec.write({"state": "stored"})
            for line in rec.line_ids:
                if line.piece_id:
                    line.piece_id.write({"state": "stored"})

    def action_open(self, reason=None):
        """拆封(退货/换货)"""
        for rec in self:
            rec.write({
                "state": "opened",
                "note": (rec.note or "") + f"\n[拆封] {reason or ''}",
            })

    @api.model
    def verify_by_qr(self, qr):
        """扫码验证包装"""
        pkg = self.search([("qr_payload", "=", qr)], limit=1)
        if not pkg:
            pkg = self.search([("name", "=", qr.split("/")[-1].split("?")[0])], limit=1)
        if not pkg:
            return {"found": False}
        return {
            "found": True,
            "name": pkg.name,
            "kind": pkg.package_kind,
            "piece_count": pkg.piece_count,
            "total_weight_g": pkg.total_weight_g,
            "ngtc_cert_no": pkg.ngtc_cert_no,
            "sealed_time": str(pkg.sealed_time) if pkg.sealed_time else None,
            "state": pkg.state,
        }


class GoldPackageLine(models.Model):
    _name = "gold.package.line"
    _description = "包装盒内件明细"
    _order = "package_id, sequence, id"

    package_id = fields.Many2one("gold.package", string="包装", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(string="序号", default=10)
    piece_id = fields.Many2one("gold.piece", string="件级 SN", required=True, index=True)
    actual_weight_g = fields.Float(string="实际重量 (g)", digits=(18, 6), related="piece_id.actual_weight_g")
    product_id = fields.Many2one("product.product", string="产品", related="piece_id.product_id")
    ngtc_cert_no = fields.Char(string="NGTC 证书号", related="piece_id.ngtc_cert_no")
    note = fields.Text(string="备注")