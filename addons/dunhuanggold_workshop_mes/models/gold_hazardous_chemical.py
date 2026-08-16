# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 危化品管理 (环 / EHS)
==========================================

作业指导书「环」要素之「安全与环保」:
  - 危化品台账: 氰化金钾 / 氰化银钾 / 盐酸 / 硝酸 / 电镀液等
  - 领用「双人双锁」: 领用人 + 保管员 + 审批人, 不可兼任
  - 库存余量实时扣减, 低于安全库存预警

模型:
  - gold.hazardous.chemical        危化品台账
  - gold.hazardous.chemical.usage  领用 / 退库记录
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

HAZARD_LEVEL_SELECTION = [
    ("high", "剧毒 (一类)"),
    ("medium", "高毒 (二类)"),
    ("low", "一般 (三类)"),
]

HAZARD_CATEGORY_SELECTION = [
    ("cyanide", "氰化物 (氰化金钾/银钾)"),
    ("acid", "酸 (盐酸/硝酸/硫酸)"),
    ("alkali", "碱"),
    ("plating", "电镀液"),
    ("organic", "有机溶剂"),
    ("other", "其他"),
]


class GoldHazardousChemical(models.Model):
    _name = "gold.hazardous.chemical"
    _description = "危化品台账"
    _order = "code"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    code = fields.Char(string="危化品编号", required=True, size=32)
    name = fields.Char(string="危化品名称", required=True)
    cas_no = fields.Char(string="CAS 号")
    category = fields.Selection(
        HAZARD_CATEGORY_SELECTION,
        string="类别",
        required=True,
    )
    danger_level = fields.Selection(
        HAZARD_LEVEL_SELECTION,
        string="危险等级",
        default="medium",
        required=True,
    )
    # 双人双锁
    lock_required = fields.Boolean(
        string="双人双锁",
        default=True,
        help="剧毒/高毒危化品必须双人双锁保管",
    )
    storage_location = fields.Char(string="存放位置", help="危化品柜编号 / 库位")
    keeper_id = fields.Many2one(
        "res.users",
        string="保管员",
        help="双锁保管人之一",
    )
    keeper2_id = fields.Many2one(
        "res.users",
        string="第二保管员",
        help="双锁第二保管人, 与保管员不可同一人",
    )
    # 库存
    stock_qty = fields.Float(string="当前库存", digits=(16, 4), default=0.0)
    stock_unit = fields.Char(string="计量单位", default="g")
    safety_stock = fields.Float(string="安全库存", digits=(16, 4), default=0.0)
    unit_price = fields.Float(string="参考单价 (元/单位)", digits=(16, 4), default=0.0)
    active = fields.Boolean(string="启用", default=True)
    note = fields.Text(string="备注")

    usage_ids = fields.One2many(
        "gold.hazardous.chemical.usage",
        "chemical_id",
        string="领用记录",
    )

    _sql_constraints = [
        ("hazchem_code_unique", "UNIQUE(code)", "危化品编号必须唯一"),
        ("hazchem_stock_positive", "CHECK(stock_qty >= 0)", "库存必须 ≥ 0"),
    ]

    @api.constrains("lock_required", "keeper_id", "keeper2_id")
    def _check_dual_custody(self):
        for rec in self:
            if rec.lock_required and rec.keeper_id and rec.keeper_id == rec.keeper2_id:
                raise ValidationError(
                    _("危化品 %s 双人双锁要求两位保管员不可为同一人") % rec.name
                )

    def consume(self, qty):
        """扣减库存"""
        self.ensure_one()
        if qty <= 0:
            raise UserError(_("领用数量必须 > 0"))
        if qty > self.stock_qty:
            raise UserError(
                _("危化品 %s 库存不足: 申请 %.4f, 现有 %.4f")
                % (self.name, qty, self.stock_qty)
            )
        self.stock_qty -= qty
        return True

    def restock(self, qty):
        """入库 / 退库"""
        self.ensure_one()
        if qty <= 0:
            raise UserError(_("入库数量必须 > 0"))
        self.stock_qty += qty
        return True

    def name_get(self):
        result = []
        for rec in self:
            display = f"[{rec.code}] {rec.name}"
            result.append((rec.id, display))
        return result


class GoldHazardousChemicalUsage(models.Model):
    _name = "gold.hazardous.chemical.usage"
    _description = "危化品领用记录"
    _order = "usage_time desc"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="领用单号",
        readonly=True,
        default=lambda self: _("新领用"),
    )
    chemical_id = fields.Many2one(
        "gold.hazardous.chemical",
        string="危化品",
        required=True,
        ondelete="restrict",
        index=True,
    )
    usage_type = fields.Selection(
        [
            ("issue", "领用出库"),
            ("return", "退库"),
            ("scrap", "报废处置"),
        ],
        string="类型",
        default="issue",
        required=True,
    )
    qty = fields.Float(string="数量", digits=(16, 4), required=True)
    unit = fields.Char(related="chemical_id.stock_unit", string="单位")
    # 三级分离: 领用人 / 保管员 / 审批人
    requester_id = fields.Many2one(
        "res.users",
        string="领用人",
        required=True,
        default=lambda self: self.env.user,
    )
    keeper_id = fields.Many2one("res.users", string="保管员", required=True)
    approver_id = fields.Many2one("res.users", string="审批人")
    # 双人双锁: 两名保管员共同开柜
    dual_custody_confirmed = fields.Boolean(
        string="双人确认",
        default=False,
        help="两名保管员共同开柜确认",
    )
    usage_time = fields.Datetime(
        string="领用时间",
        default=fields.Datetime.now,
        required=True,
        index=True,
    )
    purpose = fields.Char(string="用途")
    production_id = fields.Many2one(
        "mrp.production",
        string="关联生产订单",
        index=True,
    )
    workstation_id = fields.Many2one(
        "gold.workstation",
        string="领用工位",
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("cancelled", "已作废"),
        ],
        string="状态",
        default="draft",
        required=True,
        tracking=True,
    )
    note = fields.Text(string="备注")

    @api.model
    def create(self, vals):
        if vals.get("name", _("新领用")) == _("新领用"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "gold.hazardous.chemical.usage"
            ) or _("新领用")
        return super().create(vals)

    @api.constrains("usage_type", "requester_id", "keeper_id")
    def _check_segregation(self):
        for rec in self:
            if rec.usage_type == "issue" and rec.requester_id == rec.keeper_id:
                raise ValidationError(_("领用人与保管员不可为同一人 (职责分离)"))

    def action_confirm(self):
        """确认领用并扣减库存"""
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("仅草稿状态可确认"))
            if rec.usage_type == "issue":
                if rec.chemical_id.lock_required and not rec.dual_custody_confirmed:
                    raise UserError(
                        _("危化品 %s 需双人确认后方可领用") % rec.chemical_id.name
                    )
                rec.chemical_id.consume(rec.qty)
            elif rec.usage_type == "return":
                rec.chemical_id.restock(rec.qty)
            rec.state = "confirmed"

    def action_cancel(self):
        for rec in self:
            if rec.state == "confirmed":
                if rec.usage_type == "issue":
                    rec.chemical_id.restock(rec.qty)
                elif rec.usage_type == "return":
                    rec.chemical_id.consume(rec.qty)
            rec.state = "cancelled"

    def name_get(self):
        result = []
        for rec in self:
            display = f"{rec.name} {rec.chemical_id.name or ''}"
            result.append((rec.id, display))
        return result
