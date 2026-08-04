# -*- coding: utf-8 -*-
"""
贵金属车间 ERP — BOM 扩展
==========================

继承 mrp.bom,扩展:
  - 多阶 BOM(主件 / 金料 / 镶石 / 包装 / 焊料)
  - 工序损耗自动分摊到子件
  - 金料类型子件(如 18K / PT950)
  - 镶石子件
"""

from odoo import models, fields, api, _


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    gold_process_type = fields.Selection(
        [
            ("oil_press", "油压"),
            ("lost_wax", "失蜡"),
            ("common", "通用"),
        ],
        string="工艺归属",
        related="product_tmpl_id.gold_process_type",
        store=True,
    )
    gold_route_id = fields.Many2one(
        "gold.process.route",
        string="工艺路线",
        help="款式工艺路线",
    )
    gold_standard_weight_g = fields.Float(
        string="标准单件克重 (g)",
        digits=(18, 6),
        related="product_tmpl_id.gold_standard_weight_g",
    )
    gold_bom_type = fields.Selection(
        [
            ("finished", "成品 BOM"),
            ("wax", "蜡模 BOM"),
            ("casting", "铸件 BOM"),
            ("stone", "镶石 BOM"),
        ],
        string="BOM 类型",
        default="finished",
    )
