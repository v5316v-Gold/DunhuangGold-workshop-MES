# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 环境监测 (环 / Environment)
================================================

作业指导书「人机料法环」之「环」要素:
  - 温湿度 / 洁净度 / 照度 / 噪声 / VOC / PM2.5 实时监测
  - 超限自动预警(超上限 / 低于下限)
  - 为精密加工、钻石房、电镀车间提供合规环境证据

模型:
  - gold.environment.sensor   环境传感器台账(点位 / 类型 / 阈值 / 协议)
  - gold.environment.reading  环境读数(时序, 超限自动标记 alarm)
"""

from odoo import models, fields, api, _

ENV_SENSOR_TYPE_SELECTION = [
    ("temperature", "温度 (℃)"),
    ("humidity", "湿度 (%RH)"),
    ("cleanliness", "洁净度 (级)"),
    ("illuminance", "照度 (lux)"),
    ("noise", "噪声 (dB)"),
    ("voc", "VOC (ppm)"),
    ("pm25", "PM2.5 (mg/m³)"),
]

ENV_PROTOCOL_SELECTION = [
    ("none", "无 (人工)"),
    ("modbus_rtu", "Modbus RTU"),
    ("rs485", "RS-485"),
    ("zigbee", "ZigBee"),
    ("mqtt", "MQTT"),
    ("http_rest", "HTTP / REST"),
]


class GoldEnvironmentSensor(models.Model):
    _name = "gold.environment.sensor"
    _description = "环境传感器"
    _order = "code"
    _rec_name = "name"

    code = fields.Char(string="传感器编号", required=True, size=32)
    name = fields.Char(string="传感器名称", required=True)
    sensor_type = fields.Selection(
        ENV_SENSOR_TYPE_SELECTION,
        string="监测类型",
        required=True,
    )
    unit = fields.Char(
        string="单位",
        compute="_compute_unit",
        store=True,
    )
    location_id = fields.Many2one(
        "stock.location",
        string="监测点位",
        help="电镀车间 / 钻石房 / 抛光车间 / 金库等",
    )
    location_desc = fields.Char(string="点位描述")
    workstation_id = fields.Many2one(
        "gold.workstation",
        string="关联工位",
    )
    # 报警阈值
    alarm_min = fields.Float(string="报警下限", digits=(12, 3))
    alarm_max = fields.Float(string="报警上限", digits=(12, 3))
    # 通讯
    protocol = fields.Selection(
        ENV_PROTOCOL_SELECTION,
        string="通讯协议",
        default="none",
        required=True,
    )
    device_node_id = fields.Char(string="设备节点 ID / Topic")
    poll_interval_seconds = fields.Integer(string="采集间隔 (秒)", default=60)
    active = fields.Boolean(string="启用", default=True)
    note = fields.Text(string="备注")

    reading_ids = fields.One2many(
        "gold.environment.reading",
        "sensor_id",
        string="读数记录",
    )
    latest_reading_id = fields.Many2one(
        "gold.environment.reading",
        string="最新读数",
        compute="_compute_latest_reading",
        store=False,
    )

    _sql_constraints = [
        ("env_sensor_code_unique", "UNIQUE(code)", "传感器编号必须唯一"),
    ]

    @api.depends("sensor_type")
    def _compute_unit(self):
        unit_map = {
            "temperature": "℃",
            "humidity": "%RH",
            "cleanliness": "级",
            "illuminance": "lux",
            "noise": "dB",
            "voc": "ppm",
            "pm25": "mg/m³",
        }
        for rec in self:
            rec.unit = unit_map.get(rec.sensor_type, "")

    @api.depends("reading_ids.reading_time")
    def _compute_latest_reading(self):
        for rec in self:
            latest = self.env["gold.environment.reading"].search(
                [("sensor_id", "=", rec.id)],
                order="reading_time desc",
                limit=1,
            )
            rec.latest_reading_id = latest.id if latest else False

    def name_get(self):
        result = []
        for rec in self:
            display = f"[{rec.code}] {rec.name}"
            result.append((rec.id, display))
        return result


class GoldEnvironmentReading(models.Model):
    _name = "gold.environment.reading"
    _description = "环境读数"
    _order = "reading_time desc"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="读数编号",
        readonly=True,
        default=lambda self: _("新读数"),
    )
    sensor_id = fields.Many2one(
        "gold.environment.sensor",
        string="传感器",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sensor_type = fields.Selection(
        related="sensor_id.sensor_type",
        string="监测类型",
        store=True,
    )
    unit = fields.Char(related="sensor_id.unit", string="单位")
    value = fields.Float(string="读数", digits=(12, 3), required=True)
    reading_time = fields.Datetime(
        string="读数时间",
        default=fields.Datetime.now,
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("normal", "正常"),
            ("alarm", "超限报警"),
        ],
        string="状态",
        compute="_compute_state",
        store=True,
    )
    alarm_desc = fields.Char(string="报警说明", compute="_compute_state", store=True)
    source = fields.Selection(
        [
            ("manual", "人工录入"),
            ("device", "设备自动"),
            ("rest_api", "REST API"),
        ],
        string="来源",
        default="rest_api",
    )
    note = fields.Text(string="备注")

    @api.depends("value", "sensor_id.alarm_min", "sensor_id.alarm_max")
    def _compute_state(self):
        # 约定: alarm_min > 0 才启用下限, alarm_max > 0 才启用上限
        for rec in self:
            sensor = rec.sensor_id
            desc = ""
            state = "normal"
            if sensor:
                alarm_min = sensor.alarm_min or 0.0
                alarm_max = sensor.alarm_max or 0.0
                if alarm_min > 0 and rec.value < alarm_min:
                    state = "alarm"
                    desc = _("低于下限 %.3f %s") % (alarm_min, rec.unit or "")
                if alarm_max > 0 and rec.value > alarm_max:
                    state = "alarm"
                    desc = _("超过上限 %.3f %s") % (alarm_max, rec.unit or "")
            rec.state = state
            rec.alarm_desc = desc

    @api.model
    def create(self, vals):
        if vals.get("name", _("新读数")) == _("新读数"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "gold.environment.reading"
            ) or _("新读数")
        return super().create(vals)

    def name_get(self):
        result = []
        for rec in self:
            display = f"{rec.sensor_id.code or ''} {rec.value} {rec.unit or ''}"
            result.append((rec.id, display))
        return result
