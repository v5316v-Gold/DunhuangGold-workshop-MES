# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 能耗管理 (环 / Energy)
============================================

作业指导书「环」要素之「能源管理」:
  - 电 / 燃气 / 压缩空气 / 水 分项计量
  - 分车间 / 分设备 / 分时段
  - 单位产品能耗与碳排放核算基础

模型:
  - gold.energy.meter    能源计量表台账
  - gold.energy.reading  能耗读数(时序)
"""

from odoo import models, fields, api, _

ENERGY_TYPE_SELECTION = [
    ("electricity", "电 (kWh)"),
    ("gas", "燃气 (m³)"),
    ("compressed_air", "压缩空气 (m³)"),
    ("water", "水 (t)"),
]

METER_LEVEL_SELECTION = [
    ("plant", "厂级"),
    ("workshop", "车间级"),
    ("equipment", "设备级"),
]


class GoldEnergyMeter(models.Model):
    _name = "gold.energy.meter"
    _description = "能源计量表"
    _order = "code"
    _rec_name = "name"

    code = fields.Char(string="表计编号", required=True, size=32)
    name = fields.Char(string="表计名称", required=True)
    energy_type = fields.Selection(
        ENERGY_TYPE_SELECTION,
        string="能源类型",
        required=True,
    )
    meter_level = fields.Selection(
        METER_LEVEL_SELECTION,
        string="计量层级",
        default="workshop",
        required=True,
    )
    location_id = fields.Many2one(
        "stock.location",
        string="计量区域",
    )
    equipment_id = fields.Many2one(
        "gold.equipment",
        string="关联设备",
        help="设备级表计关联到具体设备",
    )
    unit = fields.Char(
        string="单位",
        compute="_compute_unit",
        store=True,
    )
    # 通讯
    protocol = fields.Selection(
        [
            ("none", "无 (人工抄表)"),
            ("modbus_rtu", "Modbus RTU"),
            ("rs485", "RS-485"),
            ("mqtt", "MQTT"),
            ("http_rest", "HTTP / REST"),
        ],
        string="通讯协议",
        default="none",
    )
    device_node_id = fields.Char(string="设备节点 ID / Topic")
    rate_price = fields.Float(
        string="单价 (元/单位)",
        digits=(16, 4),
        default=0.0,
        help="用于能耗金额核算",
    )
    active = fields.Boolean(string="启用", default=True)
    note = fields.Text(string="备注")

    reading_ids = fields.One2many(
        "gold.energy.reading",
        "meter_id",
        string="读数记录",
    )

    _sql_constraints = [
        ("energy_meter_code_unique", "UNIQUE(code)", "表计编号必须唯一"),
    ]

    @api.depends("energy_type")
    def _compute_unit(self):
        unit_map = {
            "electricity": "kWh",
            "gas": "m³",
            "compressed_air": "m³",
            "water": "t",
        }
        for rec in self:
            rec.unit = unit_map.get(rec.energy_type, "")

    def name_get(self):
        result = []
        for rec in self:
            display = f"[{rec.code}] {rec.name}"
            result.append((rec.id, display))
        return result


class GoldEnergyReading(models.Model):
    _name = "gold.energy.reading"
    _description = "能耗读数"
    _order = "reading_time desc"
    _rec_name = "name"

    name = fields.Char(
        string="读数编号",
        readonly=True,
        default=lambda self: _("新读数"),
    )
    meter_id = fields.Many2one(
        "gold.energy.meter",
        string="表计",
        required=True,
        ondelete="cascade",
        index=True,
    )
    energy_type = fields.Selection(
        related="meter_id.energy_type",
        string="能源类型",
        store=True,
    )
    unit = fields.Char(related="meter_id.unit", string="单位")
    # 累计读数(表底) 与 本期用量
    cumulative_value = fields.Float(
        string="累计读数",
        digits=(16, 3),
        required=True,
    )
    period_consumption = fields.Float(
        string="本期用量",
        digits=(16, 3),
        compute="_compute_period",
        store=True,
        help="相对上一读数的差值",
    )
    period_amount = fields.Float(
        string="本期金额 (元)",
        digits=(16, 2),
        compute="_compute_period",
        store=True,
    )
    reading_time = fields.Datetime(
        string="读数时间",
        default=fields.Datetime.now,
        required=True,
        index=True,
    )
    source = fields.Selection(
        [
            ("manual", "人工抄表"),
            ("device", "设备自动"),
            ("rest_api", "REST API"),
        ],
        string="来源",
        default="rest_api",
    )
    note = fields.Text(string="备注")

    @api.depends("meter_id", "cumulative_value", "reading_time")
    def _compute_period(self):
        for rec in self:
            prev = self.env["gold.energy.reading"].search(
                [
                    ("meter_id", "=", rec.meter_id.id),
                    ("reading_time", "<", rec.reading_time),
                ],
                order="reading_time desc",
                limit=1,
            )
            if prev and rec.cumulative_value >= prev.cumulative_value:
                rec.period_consumption = rec.cumulative_value - prev.cumulative_value
            else:
                rec.period_consumption = 0.0
            rec.period_amount = rec.period_consumption * (rec.meter_id.rate_price or 0.0)

    @api.model
    def create(self, vals):
        if vals.get("name", _("新读数")) == _("新读数"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "gold.energy.reading"
            ) or _("新读数")
        return super().create(vals)

    def name_get(self):
        result = []
        for rec in self:
            display = f"{rec.meter_id.code or ''} {rec.cumulative_value} {rec.unit or ''}"
            result.append((rec.id, display))
        return result
