# -*- coding: utf-8 -*-
"""
贵金属车间 ERP — 工艺路线 (mrp.routing 扩展)
=============================================

仅作为 Odoo mrp.routing 的适配,核心业务在 gold.process.route。
生产订单引用时通过 route_id 关联 gold.process.route。
"""

from odoo import models, fields


class MrpRouting(models.Model):
    _inherit = "mrp.routing"

    gold_process_type = fields.Selection(
        [
            ("oil_press", "油压"),
            ("lost_wax", "失蜡"),
        ],
        string="工艺归属",
    )
    gold_route_template_id = fields.Many2one(
        "gold.process.route",
        string="工艺路线模板",
    )
