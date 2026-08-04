# -*- coding: utf-8 -*-
"""
贵金属车间 ERP — 计量单位字典
=============================

贵金属计量的特殊性:
  - 国际单位:克(g) / 毫克(mg) / 千克(kg)
  - 港台:钱(1钱 = 3.75g) / 两(1两 = 37.5g)
  - 盎司(oz):1 金衡盎司 = 31.1034768g
  - 克拉(ct):宝石用,1ct = 0.2g

精度要求:
  - 金料称重:0.001g(毫克级)
  - XRF 含量:0.01%
  - 金价:0.01 元/g
  - 工时:0.01 小时
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class GoldMeasurement(models.Model):
    _name = "gold.measurement"
    _description = "贵金属计量单位"
    _order = "sequence, code"
    _rec_name = "name"

    code = fields.Char(
        string="单位编码",
        required=True,
        size=16,
        help="ISO/国标编码,如 g / mg / oz / ct / 钱 / 两",
    )
    name = fields.Char(
        string="单位名称",
        required=True,
        translate=True,
        help="中文/英文名称",
    )
    category = fields.Selection(
        [
            ("weight", "重量"),
            ("time", "时间"),
            ("ratio", "比率"),
            ("currency", "金额"),
            ("piece", "件数"),
        ],
        string="类别",
        required=True,
        default="weight",
    )
    # 换算到克的系数(金衡盎司固定 31.1034768)
    factor_to_gram = fields.Float(
        string="换算到克系数",
        digits=(20, 10),
        required=True,
        default=1.0,
        help="1 单位 = factor_to_gram 克。如 oz = 31.1034768",
    )
    precision_digits = fields.Integer(
        string="显示精度",
        default=3,
        help="显示/四舍五入小数位。金料称重建议 3 (= 0.001g)",
    )
    sequence = fields.Integer(string="顺序", default=10)
    active = fields.Boolean(string="有效", default=True)
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "单位编码必须唯一"),
        ("factor_positive", "CHECK(factor_to_gram > 0)", "换算系数必须大于 0"),
    ]

    @api.constrains("factor_to_gram")
    def _check_factor(self):
        for rec in self:
            if rec.factor_to_gram <= 0:
                raise ValidationError(_("换算系数必须大于 0"))

    def convert_to_gram(self, qty):
        """通用换算:单位 -> 克"""
        self.ensure_one()
        return float(qty) * self.factor_to_gram

    def convert_from_gram(self, gram):
        """通用换算:克 -> 单位"""
        self.ensure_one()
        return float(gram) / self.factor_to_gram
