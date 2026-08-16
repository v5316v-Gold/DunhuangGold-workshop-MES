# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 印记管理
==========================

依据 GB 11887-2012 §4.1,贵金属首饰必须有印记:
  - 材质印记: 金 Au / 铂 Pt / 钯 Pd / 银 Ag
  - 纯度印记: 足金 999 / 18K 750 / 14K 585 / PT950 / Pd950 / 925
  - 厂印: 企业代号 (经 NGTC 备案)
  - 检测中心印记: NGTC + 检测员代号 + 编号(委托 NGTC 检测时)

印记记录要点:
  - 印记内容
  - 位置(工位 #1 / #2 / #3)
  - 字模校对
  - 操作员 + 复核员 + 编码员 三级分离
  - 电子签名
  - 激光打字设备直采
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


IMPRINT_TYPE_SELECTION = [
    ("material", "材质印记"),
    ("purity", "纯度印记"),
    ("factory", "厂印"),
    ("assay", "检测中心印记"),
]


class GoldImprint(models.Model):
    _name = "gold.imprint"
    _description = "印记记录"
    _order = "imprint_time desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"

    name = fields.Char(
        string="印记记录号",
        required=True,
        readonly=True,
        default=lambda self: _("新印记"),
    )
    # 关联
    production_id = fields.Many2one(
        "mrp.production",
        string="生产订单",
    )
    product_id = fields.Many2one(
        "product.product",
        string="成品",
    )
    piece_sn = fields.Char(
        string="件序号",
        help="一物一码 / 一件一号",
    )
    # 印记内容
    imprint_type = fields.Selection(
        IMPRINT_TYPE_SELECTION,
        string="印记类型",
        required=True,
    )
    material_code = fields.Char(
        string="材质印记",
        size=8,
        help="Au / Pt / Pd / Ag",
    )
    purity_code = fields.Char(
        string="纯度印记",
        size=8,
        help="足金 999 / 18K 750 / PT950 / 925",
    )
    factory_code = fields.Char(
        string="厂印",
        size=8,
        help="经 NGTC 备案的企业代号",
    )
    assay_code = fields.Char(
        string="检测中心印记",
        size=16,
        help="NGTC 编号 + 检测员代号",
    )
    imprint_content = fields.Char(
        string="完整印记",
        compute="_compute_content",
        store=True,
    )
    # 位置
    imprint_position = fields.Selection(
        [
            ("inside_ring", "戒指内壁"),
            ("clasp", "扣位"),
            ("back", "背面"),
            ("inside_bangle", "手镯内壁"),
            ("chain", "链节"),
            ("other", "其他"),
        ],
        string="印记位置",
    )
    # 设备
    equipment_id = fields.Many2one(
        "gold.equipment",
        string="激光打字机",
        domain=[("category", "=", "laser_marker")],
    )
    # 人员
    operator_id = fields.Many2one(
        "res.users",
        string="操作员",
        required=True,
    )
    reviewer_id = fields.Many2one(
        "res.users",
        string="复核员",
    )
    encoder_id = fields.Many2one(
        "res.users",
        string="编码员",
    )
    imprint_time = fields.Datetime(
        string="印记时间",
        default=fields.Datetime.now,
    )
    # 验证
    ocr_verified = fields.Boolean(
        string="OCR 校验",
        default=False,
    )
    ocr_verified_time = fields.Datetime(string="OCR 校验时间")
    ocr_mismatch = fields.Boolean(string="OCR 不匹配")
    ocr_image = fields.Binary(string="OCR 截图")
    # NGTC 证书
    ngtc_cert_no = fields.Char(
        string="NGTC 证书号",
    )
    ngtc_cert_image = fields.Binary(string="NGTC 证书")
    note = fields.Text(string="备注")

    _sql_constraints = [
        (
            "three_role_separation",
            "CHECK(operator_id != reviewer_id AND operator_id != encoder_id AND reviewer_id != encoder_id)",
            "操作员、复核员、编码员三者必须分离",
        ),
    ]

    @api.depends("material_code", "purity_code", "factory_code", "assay_code")
    def _compute_content(self):
        for rec in self:
            parts = []
            if rec.material_code:
                parts.append(rec.material_code)
            if rec.purity_code:
                parts.append(rec.purity_code)
            if rec.factory_code:
                parts.append(rec.factory_code)
            if rec.assay_code:
                parts.append(rec.assay_code)
            rec.imprint_content = " ".join(parts)

    @api.model
    def create(self, vals):
        if vals.get("name", _("新印记")) == _("新印记"):
            vals["name"] = self.env["ir.sequence"].next_by_code("gold.imprint")
        return super().create(vals)

    @api.constrains("operator_id", "reviewer_id", "encoder_id")
    def _check_three_separation(self):
        for rec in self:
            ids = [rec.operator_id.id, rec.reviewer_id.id, rec.encoder_id.id]
            ids = [i for i in ids if i]
            if len(ids) != len(set(ids)):
                raise ValidationError(_("操作员/复核员/编码员三者必须分离 (GB 11887-2012 §4.1)"))

    def action_ocr_verify(self, expected):
        """OCR 校验"""
        self.ensure_one()
        if not self.imprint_content:
            raise UserError(_("印记内容为空"))
        self.ocr_verified = True
        self.ocr_verified_time = fields.Datetime.now()
        if expected and self.imprint_content.strip() != expected.strip():
            self.ocr_mismatch = True
            return False
        self.ocr_mismatch = False
        return True
