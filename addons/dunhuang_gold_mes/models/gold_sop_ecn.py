# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — SOP 与工程变更 (法 / Method)
=================================================

作业指导书「法」要素:
  - SOP 作业指导书: 关联工序, 版本化, PDF / 视频
  - ECN 工程变更: 工艺路线 / BOM 变更审批流

模型:
  - gold.sop.document  SOP 作业指导书
  - gold.ecn          工程变更单
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

SOP_DOC_TYPE_SELECTION = [
    ("pdf", "PDF 文档"),
    ("video", "视频"),
    ("image", "图片"),
    ("text", "文本"),
]

SOP_STATE_SELECTION = [
    ("draft", "草稿"),
    ("effective", "已生效"),
    ("obsolete", "已作废"),
]

ECN_TYPE_SELECTION = [
    ("routing", "工艺路线变更"),
    ("bom", "BOM 变更"),
    ("sop", "SOP 变更"),
    ("material", "物料替换"),
    ("other", "其他"),
]

ECN_STATE_SELECTION = [
    ("draft", "草稿"),
    ("review", "评审中"),
    ("approved", "已批准"),
    ("effective", "已生效"),
    ("rejected", "已驳回"),
]


class GoldSopDocument(models.Model):
    _name = "gold.sop.document"
    _description = "SOP 作业指导书"
    _order = "operation_id, version desc"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="SOP 名称", required=True)
    code = fields.Char(string="SOP 编号", required=True, size=32)
    operation_id = fields.Many2one(
        "gold.process.operation",
        string="关联工序",
        required=True,
        index=True,
        ondelete="restrict",
    )
    version = fields.Char(string="版本", default="V1.0", required=True)
    document_type = fields.Selection(
        SOP_DOC_TYPE_SELECTION,
        string="文档类型",
        default="pdf",
        required=True,
    )
    state = fields.Selection(
        SOP_STATE_SELECTION,
        string="状态",
        default="draft",
        required=True,
        tracking=True,
    )
    author_id = fields.Many2one(
        "res.users",
        string="编写人",
        default=lambda self: self.env.user,
    )
    effective_date = fields.Date(string="生效日期")
    review_date = fields.Date(string="复审日期")
    content = fields.Html(string="正文 (文本 SOP)")
    attachment = fields.Binary(string="附件")
    attachment_filename = fields.Char(string="附件文件名")
    keywords = fields.Char(string="关键词")
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("sop_code_unique", "UNIQUE(code, version)", "SOP 编号+版本必须唯一"),
    ]

    def action_effective(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("仅草稿状态可生效"))
            rec.state = "effective"
            rec.effective_date = rec.effective_date or fields.Date.context_today(self)

    def action_obsolete(self):
        for rec in self:
            rec.state = "obsolete"

    def name_get(self):
        result = []
        for rec in self:
            display = f"[{rec.code}] {rec.name} {rec.version}"
            result.append((rec.id, display))
        return result


class GoldEcn(models.Model):
    _name = "gold.ecn"
    _description = "工程变更单 (ECN)"
    _order = "code desc"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="变更单号",
        readonly=True,
        default=lambda self: _("新变更"),
    )
    code = fields.Char(string="变更编号", size=32)
    title = fields.Char(string="变更标题", required=True)
    change_type = fields.Selection(
        ECN_TYPE_SELECTION,
        string="变更类型",
        required=True,
        default="routing",
    )
    state = fields.Selection(
        ECN_STATE_SELECTION,
        string="状态",
        default="draft",
        required=True,
        tracking=True,
    )
    route_id = fields.Many2one(
        "gold.process.route",
        string="关联工艺路线",
    )
    bom_id = fields.Many2one(
        "mrp.bom",
        string="关联 BOM",
    )
    operation_id = fields.Many2one(
        "gold.process.operation",
        string="关联工序",
    )
    reason = fields.Text(string="变更原因", required=True)
    change_content = fields.Text(string="变更内容", required=True)
    impact_analysis = fields.Text(string="影响分析")
    proposed_by = fields.Many2one(
        "res.users",
        string="提出人",
        default=lambda self: self.env.user,
    )
    approved_by = fields.Many2one(
        "res.users",
        string="批准人",
    )
    effective_date = fields.Date(string="生效日期")
    note = fields.Text(string="备注")

    @api.model
    def create(self, vals):
        if vals.get("name", _("新变更")) == _("新变更"):
            vals["name"] = self.env["ir.sequence"].next_by_code("gold.ecn") or _("新变更")
        return super().create(vals)

    def action_submit(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("仅草稿状态可提交评审"))
            rec.state = "review"

    def action_approve(self):
        for rec in self:
            if rec.state != "review":
                raise UserError(_("仅评审中状态可批准"))
            rec.state = "approved"
            rec.approved_by = self.env.user

    def action_effective(self):
        for rec in self:
            if rec.state != "approved":
                raise UserError(_("仅已批准状态可生效"))
            rec.state = "effective"
            rec.effective_date = rec.effective_date or fields.Date.context_today(self)

    def action_reject(self):
        for rec in self:
            if rec.state not in ("draft", "review"):
                raise UserError(_("当前状态不可驳回"))
            rec.state = "rejected"

    def name_get(self):
        result = []
        for rec in self:
            display = f"{rec.name} {rec.title}"
            result.append((rec.id, display))
        return result
