"""
敦煌金加工车间 ERP — 工位
=========================

工位 = 物理作业点 + 人员 + 设备 + 关联工序

工位类型:
  - 油压工位: 落料 + 油压 + 切边
  - 蜡模工位: 雕蜡 + 3D 打印 + 树
  - 铸造工位: 灌石膏 + 焙烧 + 熔金浇铸
  - 精加工工位: 执模 + 镶石 + 抛光
  - 印记工位: 激光打字
  - 检验工位: XRF + 重量 + 印记校验
  - 金库工位: 出入库
  - 委外工位: 外协收发货
"""

from odoo import models, fields


WORKSTATION_TYPE_SELECTION = [
    ("oil_press", "油压工位"),
    ("wax", "蜡模工位"),
    ("casting", "铸造工位"),
    ("finishing", "精加工工位"),
    ("marking", "印记工位"),
    ("qc", "质检工位"),
    ("vault", "金库工位"),
    ("outsource", "委外工位"),
]


class GoldWorkstation(models.Model):
    _name = "gold.workstation"
    _description = "车间工位"
    _order = "code"
    _rec_name = "name"

    code = fields.Char(string="工位编码", required=True, size=16)
    name = fields.Char(string="工位名称", required=True)
    workstation_type = fields.Selection(
        WORKSTATION_TYPE_SELECTION,
        string="工位类型",
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
    location = fields.Char(string="位置")
    leader_id = fields.Many2one(
        "res.users",
        string="班组长",
    )
    equipment_ids = fields.One2many(
        "gold.equipment",
        "workshop_id",
        string="设备列表",
    )
    operation_ids = fields.Many2many(
        "gold.process.operation",
        string="允许工序",
    )
    active = fields.Boolean(string="启用", default=True)
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "工位编码必须唯一"),
    ]

    def name_get(self):
        result = []
        for rec in self:
            display = f"[{rec.code}] {rec.name}"
            result.append((rec.id, display))
        return result
