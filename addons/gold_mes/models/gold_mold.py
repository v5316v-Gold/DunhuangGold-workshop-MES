# -*- coding: utf-8 -*-
"""
贵金属车间 ERP — 模具管理(油压专属)
====================================

模具台账:
  - 模具编号 / 款式 / 材质 / 产地 / 寿命
  - 使用次数累计 / 寿命预警
  - 维修 / 报废 / 备模
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


MOLD_STATE_SELECTION = [
    ("new", "新品"),
    ("in_use", "使用中"),
    ("idle", "闲置"),
    ("maintenance", "保养中"),
    ("scrapped", "报废"),
]


MOLD_TYPE_SELECTION = [
    ("steel", "钢模"),
    ("carbide", "硬质合金"),
    ("rubber", "橡胶模"),
    ("silicone", "硅胶模"),
    ("resin", "树脂模"),
]


class GoldMold(models.Model):
    _name = "gold.mold"
    _description = "油压模具台账"
    _order = "code"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    code = fields.Char(
        string="模具编号",
        required=True,
        readonly=True,
        default=lambda self: _("新模具"),
    )
    name = fields.Char(
        string="模具名称",
        required=True,
    )
    mold_type = fields.Selection(
        MOLD_TYPE_SELECTION,
        string="模具类型",
        default="steel",
        required=True,
    )
    material = fields.Char(string="模具材质")
    manufacturer = fields.Char(string="制造商")
    style_id = fields.Many2one(
        "product.product",
        string="对应款式",
        help="模具对应的产品款式",
    )
    # 寿命
    rated_life_count = fields.Integer(
        string="额定寿命 (次数)",
        default=1000000,
        help="钢模典型 100 万次",
    )
    used_count = fields.Integer(
        string="已用次数",
        default=0,
    )
    remaining_count = fields.Integer(
        string="剩余次数",
        compute="_compute_remaining",
        store=True,
    )
    life_warning_pct = fields.Float(
        string="寿命预警阈值 (%)",
        default=10.0,
        digits=(6, 2),
        help="剩余寿命 < 额定寿命 × 阈值 触发预警",
    )
    # 状态
    state = fields.Selection(
        MOLD_STATE_SELECTION,
        string="状态",
        default="new",
        required=True,
        tracking=True,
    )
    current_equipment_id = fields.Many2one(
        "gold.equipment",
        string="当前安装设备",
        help="油压机",
    )
    # 资产
    purchase_date = fields.Date(string="购置日期")
    purchase_value = fields.Float(string="购置金额", digits=(16, 2))
    # 维修
    last_maintenance_date = fields.Date(string="上次保养")
    next_maintenance_count = fields.Integer(
        string="下次保养次数",
        default=50000,
    )
    maintenance_history_ids = fields.One2many(
        "gold.mold.maintenance",
        "mold_id",
        string="保养记录",
    )
    active = fields.Boolean(string="启用", default=True)
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "模具编号必须唯一"),
        (
            "used_lte_rated",
            "CHECK(used_count <= rated_life_count)",
            "已用次数不能超过额定寿命",
        ),
    ]

    @api.depends("rated_life_count", "used_count")
    def _compute_remaining(self):
        for rec in self:
            rec.remaining_count = max(0, rec.rated_life_count - rec.used_count)

    @api.model
    def create(self, vals):
        if vals.get("code", _("新模具")) == _("新模具"):
            vals["code"] = self.env["ir.sequence"].next_by_code("gold.mold")
        return super().create(vals)

    def action_install(self, equipment_id):
        """安装模具,自动卸载同设备前的模具"""
        self.ensure_one()
        if self.state == "scrapped":
            raise UserError(_("报废模具不可安装"))
        # 同一设备上如果已有模具,先卸载
        previous = self.search([("current_equipment_id", "=", equipment_id), ("id", "!=", self.id)])
        for prev in previous:
            prev.current_equipment_id = False
            if prev.state == "in_use":
                prev.state = "idle"
        self.current_equipment_id = equipment_id
        self.state = "in_use"
        # 同步到设备
        equipment = self.env["gold.equipment"].browse(equipment_id)
        equipment.mounted_mold_id = self.id

    def action_uninstall(self):
        self.ensure_one()
        if self.current_equipment_id:
            self.current_equipment_id.mounted_mold_id = False
        self.current_equipment_id = False
        if self.state == "in_use":
            self.state = "idle"

    def action_add_usage(self, count=1):
        """累计使用次数,达到预警触发"""
        self.ensure_one()
        self.used_count += count
        if self.remaining_count <= self.rated_life_count * (self.life_warning_pct / 100.0):
            self.message_post(
                body=_("⚠️ 模具 %s 已用 %d 次, 剩余 %d 次 (额定 %d), 接近寿命阈值 %.1f%%")
                % (self.code, self.used_count, self.remaining_count, self.rated_life_count, self.life_warning_pct)
            )
        if self.remaining_count <= 0:
            self.state = "scrapped"
            self.message_post(body=_("🔴 模具 %s 已达到额定寿命,自动报废") % self.code)

    def action_scrap(self):
        for rec in self:
            if rec.current_equipment_id:
                rec.action_uninstall()
            rec.state = "scrapped"

    def name_get(self):
        result = []
        for rec in self:
            display = f"[{rec.code}] {rec.name}"
            result.append((rec.id, display))
        return result


class GoldMoldMaintenance(models.Model):
    _name = "gold.mold.maintenance"
    _description = "模具保养记录"
    _order = "date desc, id desc"

    mold_id = fields.Many2one(
        "gold.mold",
        string="模具",
        required=True,
        ondelete="cascade",
    )
    date = fields.Date(
        string="保养日期",
        required=True,
        default=fields.Date.context_today,
    )
    operator_id = fields.Many2one(
        "res.users",
        string="操作员",
    )
    description = fields.Text(
        string="保养内容",
        required=True,
    )
    parts_used = fields.Char(string="使用配件")
    cost = fields.Float(string="费用", digits=(16, 2))
    used_count_snapshot = fields.Integer(
        string="保养时已用次数",
    )
