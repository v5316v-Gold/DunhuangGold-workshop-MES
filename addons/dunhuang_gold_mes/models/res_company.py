# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    # 车间专用字段
    gold_factory_code = fields.Char(
        string="厂印代号",
        size=8,
        help="GB 11887-2012 §4.1 厂印,需在 NGTC 备案",
    )
    gold_ngrc_cert_no = fields.Char(
        string="NGTC 备案号",
        size=32,
        help="国家首饰质量监督检验中心备案号",
    )
    gold_default_gold_metal_id = fields.Many2one(
        "product.template",
        string="默认金料材质",
        help="车间默认金料,用于新建物料批量填充",
    )
    gold_loss_tolerance_pct = fields.Float(
        string="损耗预警阈值 (%)",
        default=20.0,
        digits=(6, 2),
        help="工序实际损耗 > 定额 × (1 + 阈值) 触发预警",
    )
    gold_xrf_min_pct = fields.Float(
        string="XRF 含量下限 (%)",
        default=99.00,
        digits=(6, 2),
        help="足金 / 18K / PT950 等成色下限,详见 GB 11887-2012",
    )
    gold_price_lock_default_minutes = fields.Integer(
        string="默认金价锁价时长 (分钟)",
        default=30,
        help="订单报价时默认金价锁定时长",
    )
