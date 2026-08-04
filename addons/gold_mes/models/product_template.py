# -*- coding: utf-8 -*-
"""
贵金属车间 ERP — 产品(物料)扩展
=================================

继承 product.template,扩展贵金属专属字段:
  - 成色 / 印记
  - 工艺归属(油压 / 失蜡 / 共用)
  - 关联工艺路线模板
  - 实时计价 - 联动金价
"""

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    gold_metal_type = fields.Selection(
        related="categ_id.gold_metal_type",
        string="贵金属类型",
    )
    gold_purity = fields.Float(
        string="成色 (%)",
        digits=(6, 2),
        help="贵金属纯度,如 足金 99.99 / 18K 75.0 / PT950 95.0",
    )
    gold_imprint_code = fields.Char(
        string="印记代码",
        size=8,
        help="GB 11887-2012 §4.1 印记,如 足金 / 18K / PT950",
    )
    gold_process_type = fields.Selection(
        [
            ("oil_press", "油压"),
            ("lost_wax", "失蜡"),
            ("common", "通用"),
        ],
        string="工艺归属",
        default="common",
    )
    gold_route_id = fields.Many2one(
        "gold.process.route",
        string="工艺路线模板",
        help="产品工艺路线,生成生产订单时沿用",
    )
    gold_is_recycle = fields.Boolean(
        string="回收料",
        default=False,
    )
    gold_standard_weight_g = fields.Float(
        string="标准单件重量 (g)",
        digits=(18, 6),
        help="款式标准单件重量,用于 BOM 物料用量",
    )
    gold_allow_substitute = fields.Boolean(
        string="允许成色替代",
        default=False,
        help="如 18K ↔ PT950 跨材质替代",
    )
