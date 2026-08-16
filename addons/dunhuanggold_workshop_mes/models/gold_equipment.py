# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 设备台账
=========================

设备分为两大类:
  - 加工设备:油压机 / 落料机 / 切边机 / 失蜡炉 / 离心机 / 3D 打印机 / 激光焊 / 激光打字 / 抛光 / 电镀
  - 检测设备:电子天平 / XRF / 卡尺

关键数据:
  - 设备编号 / 名称 / 类别 / 工艺归属
  - 购置日期 / 折旧 / 净值
  - 上次校准 / 下次校准 / 校准证书
  - 通讯协议 / IP / 端口 / 节点 ID (用于 OPC UA / MQTT 接入)
  - OEE 数据(运行时长 / 故障时长 / 良品数 / 总数)
  - 模具挂载(油压机的模具)
"""

from odoo import models, fields, api, _


EQUIPMENT_CATEGORY_SELECTION = [
    # 加工
    ("oil_press_machine", "油压机"),
    ("blanking_machine", "落料机"),
    ("trimming_machine", "切边机"),
    ("wax_carver", "雕蜡机"),
    ("sla_printer", "3D 打印机 (SLA/DLP)"),
    ("lost_wax_furnace", "失蜡炉"),
    ("centrifugal_caster", "离心铸造机"),
    ("vacuum_investor", "真空灌浆机"),
    ("burnout_furnace", "焙烧炉"),
    ("melting_furnace", "熔金炉"),
    ("laser_welder", "激光焊机"),
    ("laser_marker", "激光打字机"),
    ("polishing_machine", "抛光机"),
    ("magnetic_polisher", "磁力抛光机"),
    ("plating_tank", "电镀槽"),
    # 检测
    ("xrf", "XRF 含量检测"),
    ("balance", "电子天平"),
    ("caliper", "卡尺 / 三坐标"),
    ("furnace_pyrometer", "炉温仪"),
]


PROTOCOL_SELECTION = [
    ("none", "无 (人工)"),
    ("opc_ua", "OPC UA"),
    ("modbus_tcp", "Modbus TCP"),
    ("modbus_rtu", "Modbus RTU"),
    ("mqtt", "MQTT"),
    ("http_rest", "HTTP / REST"),
    ("rs232", "RS-232 (电子天平)"),
    ("rs485", "RS-485"),
    ("mtconnect", "MTConnect"),
]


class GoldEquipment(models.Model):
    _name = "gold.equipment"
    _description = "车间设备台账"
    _order = "code"
    _rec_name = "name"

    code = fields.Char(string="设备编号", required=True, size=32, index=True)
    name = fields.Char(string="设备名称", required=True)
    category = fields.Selection(
        EQUIPMENT_CATEGORY_SELECTION,
        string="设备类别",
        required=True,
    )
    process_type = fields.Selection(
        [
            ("oil_press", "油压"),
            ("lost_wax", "失蜡"),
            ("common", "共用"),
        ],
        string="工艺归属",
        required=True,
    )
    manufacturer = fields.Char(string="厂商")
    model = fields.Char(string="型号")
    serial_no = fields.Char(string="序列号")
    workshop_id = fields.Many2one(
        "gold.workstation",
        string="所在工位",
    )
    # 状态
    state = fields.Selection(
        [
            ("idle", "空闲"),
            ("running", "运行"),
            ("down", "故障"),
            ("maintenance", "保养"),
            ("scrapped", "报废"),
        ],
        string="设备状态",
        default="idle",
    )
    # 资产
    purchase_date = fields.Date(string="购置日期")
    purchase_value = fields.Float(string="购置金额", digits=(16, 2))
    salvage_value = fields.Float(string="残值", digits=(16, 2))
    useful_life_months = fields.Integer(string="使用年限(月)")
    # 校准
    last_calibration_date = fields.Date(string="上次校准")
    next_calibration_date = fields.Date(string="下次校准")
    calibration_cert_no = fields.Char(string="校准证书号")
    # 通讯
    protocol = fields.Selection(
        PROTOCOL_SELECTION,
        string="通讯协议",
        default="none",
        required=True,
    )
    ip_address = fields.Char(string="IP 地址")
    port = fields.Integer(string="端口")
    device_node_id = fields.Char(
        string="设备节点 ID",
        help="OPC UA NodeId / MQTT Topic / REST Path",
    )
    poll_interval_seconds = fields.Integer(
        string="采集间隔 (秒)",
        default=5,
    )
    # OEE 数据(在报工和设备心跳中累积)
    oee_runtime_hours = fields.Float(
        string="累计运行 (小时)",
        digits=(16, 2),
        default=0.0,
    )
    oee_downtime_hours = fields.Float(
        string="累计故障 (小时)",
        digits=(16, 2),
        default=0.0,
    )
    oee_total_count = fields.Integer(string="累计产量", default=0)
    oee_good_count = fields.Integer(string="累计良品", default=0)
    oee = fields.Float(
        string="OEE (%)",
        compute="_compute_oee",
        digits=(6, 2),
    )
    # 模具挂载(油压机)
    mounted_mold_id = fields.Many2one(
        "gold.mold",
        string="当前模具",
        help="油压机当前挂载的模具",
    )
    active = fields.Boolean(string="启用", default=True)
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "设备编号必须唯一"),
        ("serial_unique", "UNIQUE(serial_no)", "序列号必须唯一"),
    ]

    @api.depends(
        "oee_runtime_hours",
        "oee_downtime_hours",
        "oee_total_count",
        "oee_good_count",
    )
    def _compute_oee(self):
        for rec in self:
            total_time = rec.oee_runtime_hours + rec.oee_downtime_hours
            if total_time <= 0:
                rec.oee = 0.0
                continue
            availability = rec.oee_runtime_hours / total_time
            performance = rec.oee_runtime_hours / rec.oee_runtime_hours if rec.oee_runtime_hours else 0
            quality = rec.oee_good_count / rec.oee_total_count if rec.oee_total_count else 0
            rec.oee = availability * performance * quality * 100.0

    def name_get(self):
        result = []
        for rec in self:
            display = f"[{rec.code}] {rec.name}"
            result.append((rec.id, display))
        return result
