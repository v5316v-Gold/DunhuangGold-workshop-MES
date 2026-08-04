# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # 车间专用设置
    gold_factory_code = fields.Char(
        related="company_id.gold_factory_code",
        readonly=False,
        string="厂印代号",
    )
    gold_ngrc_cert_no = fields.Char(
        related="company_id.gold_ngrc_cert_no",
        readonly=False,
        string="NGTC 备案号",
    )
    gold_loss_tolerance_pct = fields.Float(
        related="company_id.gold_loss_tolerance_pct",
        readonly=False,
        string="损耗预警阈值 (%)",
    )
    gold_xrf_min_pct = fields.Float(
        related="company_id.gold_xrf_min_pct",
        readonly=False,
        string="XRF 含量下限 (%)",
    )
    gold_price_lock_default_minutes = fields.Integer(
        related="company_id.gold_price_lock_default_minutes",
        readonly=False,
        string="默认金价锁价时长 (分钟)",
    )
