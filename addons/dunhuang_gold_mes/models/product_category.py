# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = "product.category"

    # 贵金属分类属性
    gold_metal_type = fields.Selection(
        [
            ("", "非贵金属"),
            ("fine_gold", "足金 (≥99.0%)"),
            ("k_gold", "K 金"),
            ("platinum", "铂金"),
            ("palladium", "钯金"),
            ("silver", "银"),
            ("recycle", "回收料"),
            ("solder", "焊料"),
            ("stone", "宝石"),
            ("chemical", "化工"),
            ("packaging", "包装"),
        ],
        string="贵金属类型",
        default="",
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
