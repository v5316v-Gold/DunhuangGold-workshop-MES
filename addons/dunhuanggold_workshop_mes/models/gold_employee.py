# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 人员管理 (人 / Man)
==========================================

作业指导书「人机料法环」之「人」要素:
  - 资质证书矩阵: 熔金证 / 特种作业 / 镶石技能等级 / 电镀危化品操作证
  - 资质有效期自动校验, 过期预警(作业指导书: 资质过期自动停工)
  - 考勤 / 工时: 班次 + 打卡 + 工时, 为计件与绩效提供数据源

模型:
  - gold.employee.certificate  员工资质证书
  - gold.work.attendance       考勤 / 工时记录
"""

from odoo import models, fields, api, _

CERT_TYPE_SELECTION = [
    ("melting", "熔金操作证"),
    ("special_operation", "特种作业证"),
    ("stone_setting", "镶石技能等级"),
    ("electroplating", "危化品操作证 (电镀)"),
    ("inspector", "首饰检验员证"),
    ("forklift", "特种设备作业证"),
    ("first_aid", "急救证"),
    ("other", "其他"),
]

CERT_LEVEL_SELECTION = [
    ("junior", "初级"),
    ("intermediate", "中级"),
    ("senior", "高级"),
    ("technician", "技师"),
]


class GoldEmployeeCertificate(models.Model):
    _name = "gold.employee.certificate"
    _description = "员工资质证书"
    _order = "holder_id, expiry_date"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="证书名称", required=True)
    cert_no = fields.Char(string="证书编号")
    cert_type = fields.Selection(
        CERT_TYPE_SELECTION,
        string="证书类型",
        required=True,
    )
    cert_level = fields.Selection(
        CERT_LEVEL_SELECTION,
        string="技能等级",
    )
    holder_id = fields.Many2one(
        "res.users",
        string="持证人",
        required=True,
        index=True,
        ondelete="restrict",
    )
    issuing_authority = fields.Char(string="发证机构")
    issue_date = fields.Date(string="发证日期")
    expiry_date = fields.Date(string="到期日期", required=True)
    is_valid = fields.Boolean(
        string="当前有效",
        compute="_compute_is_valid",
        store=True,
    )
    days_to_expire = fields.Integer(
        string="距到期天数",
        compute="_compute_is_valid",
        store=True,
    )
    cert_attachment = fields.Binary(string="证书扫描件")
    cert_filename = fields.Char(string="文件名")
    active = fields.Boolean(string="启用", default=True)
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("employee_cert_unique", "UNIQUE(cert_no)", "证书编号必须唯一"),
    ]

    @api.depends("expiry_date")
    def _compute_is_valid(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if not rec.expiry_date:
                rec.is_valid = False
                rec.days_to_expire = 0
                continue
            delta = (rec.expiry_date - today).days
            rec.days_to_expire = delta
            rec.is_valid = delta >= 0

    def name_get(self):
        result = []
        for rec in self:
            holder = rec.holder_id.name or ""
            display = f"{rec.name} ({holder})"
            result.append((rec.id, display))
        return result


ATTENDANCE_SHIFT_SELECTION = [
    ("day", "白班"),
    ("night", "夜班"),
    ("overtime", "加班"),
]


class GoldWorkAttendance(models.Model):
    _name = "gold.work.attendance"
    _description = "考勤 / 工时记录"
    _order = "shift_date desc, check_in"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="考勤编号",
        readonly=True,
        default=lambda self: _("新考勤"),
    )
    employee_id = fields.Many2one(
        "res.users",
        string="员工",
        required=True,
        index=True,
        ondelete="restrict",
    )
    shift_date = fields.Date(
        string="班次日期",
        default=fields.Date.context_today,
        required=True,
    )
    shift_type = fields.Selection(
        ATTENDANCE_SHIFT_SELECTION,
        string="班次",
        default="day",
        required=True,
    )
    workstation_id = fields.Many2one(
        "gold.workstation",
        string="所在工位",
    )
    check_in = fields.Datetime(string="上班时间")
    check_out = fields.Datetime(string="下班时间")
    work_hours = fields.Float(
        string="工时 (小时)",
        digits=(10, 2),
        compute="_compute_work_hours",
        store=True,
    )
    # 与报工关联, 用于绩效
    report_count = fields.Integer(
        string="报工数",
        compute="_compute_report_count",
        store=False,
    )
    output_weight_g = fields.Float(
        string="产出重量 (g)",
        digits=(18, 6),
        compute="_compute_report_count",
        store=False,
    )
    attendance_state = fields.Selection(
        [
            ("normal", "正常"),
            ("late", "迟到"),
            ("early_leave", "早退"),
            ("absent", "缺勤"),
            ("leave", "请假"),
        ],
        string="考勤状态",
        default="normal",
        required=True,
    )
    note = fields.Text(string="备注")

    _sql_constraints = [
        (
            "attendance_unique_day",
            "UNIQUE(employee_id, shift_date, shift_type)",
            "同一员工同日同班次不可重复打卡",
        ),
    ]

    @api.depends("check_in", "check_out")
    def _compute_work_hours(self):
        for rec in self:
            if rec.check_in and rec.check_out and rec.check_out > rec.check_in:
                delta = rec.check_out - rec.check_in
                rec.work_hours = delta.total_seconds() / 3600.0
            else:
                rec.work_hours = 0.0

    @api.depends("employee_id", "shift_date")
    def _compute_report_count(self):
        for rec in self:
            reports = self.env["gold.workorder.report"].search([
                ("operator_id", "=", rec.employee_id.id),
                ("report_time", ">=", rec.shift_date),
                ("report_time", "<", fields.Date.add(rec.shift_date, days=1)),
            ])
            rec.report_count = len(reports)
            rec.output_weight_g = sum(reports.mapped("output_weight_g") or [0.0])

    @api.model
    def create(self, vals):
        if vals.get("name", _("新考勤")) == _("新考勤"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "gold.work.attendance"
            ) or _("新考勤")
        return super().create(vals)

    def name_get(self):
        result = []
        for rec in self:
            display = f"{rec.employee_id.name or ''} {rec.shift_date}"
            result.append((rec.id, display))
        return result
