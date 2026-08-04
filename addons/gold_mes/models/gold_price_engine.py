# -*- coding: utf-8 -*-
"""
贵金属车间 ERP — 实时金价引擎
==============================

金价源:
  - 上海黄金交易所 (SGE) Au99.99 / Au99.95 / Au100g
  - 国际金价 LBMA London Fix
  - 银行点对点报价

金价用途:
  - 订单成本: 实时金价 × (重量 + 损耗)
  - 库存估值: 实时金价 × 可用重量
  - 旧金回收: 当日金价 × 折价系数
  - 订单报价: 订单锁价(15分钟 / 30分钟 / 1小时 / 当日)

字段:
  - 批次价: 历史回放查询
  - 实时价: 由 API/手工覆盖获得
  - 锁价: 订单报价时锁定
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


PRICE_SOURCE_SELECTION = [
    ("sge", "上海黄金交易所 SGE"),
    ("lbma", "LBMA London Fix"),
    ("china_bank", "中国银行"),
    ("manual", "手工录入"),
    ("api", "API 推送"),
]


class GoldPriceEngine(models.Model):
    _name = "gold.price.engine"
    _description = "实时金价引擎"
    _order = "price_time desc, id desc"
    _rec_name = "price_time"

    price_time = fields.Datetime(
        string="报价时间",
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    source = fields.Selection(
        PRICE_SOURCE_SELECTION,
        string="报价源",
        default="sge",
        required=True,
    )
    gold_type = fields.Selection(
        [
            ("au9999", "Au99.99"),
            ("au9995", "Au99.95"),
            ("au100g", "Au100g"),
            ("pt9995", "Pt99.95"),
            ("pd9995", "Pd99.95"),
            ("ag9999", "Ag99.99"),
            ("k18", "18K"),
            ("k24", "24K"),
        ],
        string="品种",
        default="au9999",
        required=True,
    )
    # 价格
    price_open = fields.Float(
        string="开盘价 (元/g)",
        digits=(18, 4),
    )
    price_high = fields.Float(
        string="最高价 (元/g)",
        digits=(18, 4),
    )
    price_low = fields.Float(
        string="最低价 (元/g)",
        digits=(18, 4),
    )
    price_close = fields.Float(
        string="收盘价 (元/g)",
        digits=(18, 4),
        required=True,
    )
    price_change = fields.Float(
        string="涨跌 (元/g)",
        digits=(18, 4),
        compute="_compute_change",
        store=True,
    )
    price_change_pct = fields.Float(
        string="涨跌幅 (%)",
        digits=(8, 4),
        compute="_compute_change",
        store=True,
    )
    # 详细
    unit = fields.Char(
        string="单位",
        default="元/g",
        size=16,
    )
    volume_kg = fields.Float(
        string="成交量 (kg)",
        digits=(16, 4),
    )
    open_interest = fields.Float(
        string="持仓量",
        digits=(16, 4),
    )
    is_settlement = fields.Boolean(
        string="是否结算价",
        default=False,
        help="True 用于当日所有业务结算",
    )
    note = fields.Char(string="备注")

    _sql_constraints = [
        (
            "uniq_time_source_type",
            "UNIQUE(price_time, source, gold_type)",
            "同一时间/源/品种不允许重复",
        ),
    ]

    @api.depends("price_open", "price_close")
    def _compute_change(self):
        for rec in self:
            if rec.price_open:
                rec.price_change = rec.price_close - rec.price_open
                rec.price_change_pct = (rec.price_change / rec.price_open) * 100
            else:
                rec.price_change = 0.0
                rec.price_change_pct = 0.0

    @api.model
    def get_current_price(self, gold_type="au9999", source="sge", price_time=None):
        """
        获取当前金价,缺省取当日最近结算价
        """
        domain = [
            ("gold_type", "=", gold_type),
            ("source", "=", source),
        ]
        if price_time:
            domain.append(("price_time", "<=", price_time))
        rec = self.search(domain, order="price_time desc", limit=1)
        if not rec:
            return 0.0
        return rec.price_close

    @api.model
    def lock_price(self, gold_type="au9999", lock_minutes=30, source="sge"):
        """
        锁价:返回一个 locked_price,配合订单使用
        """
        rec = self.get_current_price(gold_type, source)
        return {
            "price": rec,
            "lock_time": fields.Datetime.now(),
            "lock_until": fields.Datetime.to_string(
                fields.Datetime.add(fields.Datetime.now(), minutes=lock_minutes)
            ),
            "lock_minutes": lock_minutes,
        }

    @api.model
    def update_batch_prices(self):
        """
        刷新所有金料批次的当前金价(由 cron / API 触发)
        """
        batches = self.search([("state", "in", ["available", "locked"])])
        for batch in batches:
            gold_type = "au9999"
            if batch.gold_metal_type == "platinum":
                gold_type = "pt9995"
            elif batch.gold_metal_type == "palladium":
                gold_type = "pd9995"
            elif batch.gold_metal_type == "silver":
                gold_type = "ag9999"
            price = self.get_current_price(gold_type)
            batch.current_price = price
        return True
