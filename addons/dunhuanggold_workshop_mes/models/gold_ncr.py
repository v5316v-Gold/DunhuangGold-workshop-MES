# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — NCR (Non-Conformance Report) 不合格品处理
================================================================

Phase 3.2: 当质检/工序判定为不合格时,生成 NCR,跟踪处置:
  1. 返工 (Rework) - 重新加工
  2. 让步放行 (Concession) - 标次品,降价销售
  3. 报废 (Scrap) - 销毁/回炉
  4. 退回 (Return) - 退回上一道工序

NCR 触发源:
  - 工序报工 quality_state = failed
  - 印记 OCR 校验 mismatch
  - XRF 检测不合格 (含量低于 standard)
  - 质检点 result = failed

NCR 编号规则: NCR-YYYYMMDD-XXXX
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


NCR_DISPOSITION = [
    ("pending", "待处置"),
    ("rework", "返工"),
    ("concession", "让步放行"),
    ("scrap", "报废"),
    ("return", "退回上工序"),
    ("closed", "已关闭"),
]


NCR_SOURCE = [
    ("workorder_report", "工序报工"),
    ("imprint_ocr", "印记 OCR"),
    ("xrf", "XRF 检测"),
    ("quality_inspection", "质检"),
    ("manual", "手工录入"),
]


class GoldNcr(models.Model):
    _name = "gold.ncr"
    _description = "NCR 不合格品处理单"
    _order = "ncr_time desc, id desc"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="NCR 编号",
        required=True,
        readonly=True,
        default=lambda self: _("新 NCR"),
    )
    ncr_time = fields.Datetime(
        string="不合格发现时间",
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    # 来源
    source = fields.Selection(
        NCR_SOURCE,
        string="来源",
        required=True,
    )
    source_model = fields.Char(string="来源模型", help="如 gold.workorder.report")
    source_id = fields.Integer(string="来源记录 ID", index=True)
    # 关联
    piece_id = fields.Many2one(
        "gold.piece",
        string="件级 SN",
        index=True,
    )
    production_id = fields.Many2one(
        "mrp.production",
        string="生产订单",
        related="piece_id.production_id",
        store=True,
    )
    workorder_report_id = fields.Many2one(
        "gold.workorder.report",
        string="关联工序报工",
    )
    # 不合格描述
    defect_type = fields.Char(
        string="缺陷类型",
        help="如:划痕 / 凹陷 / 错镶 / 漏镶 / 含量不足 / 字印模糊",
    )
    defect_description = fields.Text(string="缺陷描述", required=True)
    defect_image = fields.Binary(string="缺陷照片", help="现场拍照存档")
    # 处置
    disposition = fields.Selection(
        NCR_DISPOSITION,
        string="处置决定",
        default="pending",
        required=True,
        tracking=True,
        index=True,
    )
    disposition_note = fields.Text(string="处置说明")
    disposition_time = fields.Datetime(string="处置时间")
    disposition_by_id = fields.Many2one(
        "res.users",
        string="处置人(班组长/主任)",
    )
    # 数量 / 价值
    defect_weight_g = fields.Float(
        string="不合格件重量 (g)",
        digits=(18, 6),
        help="用于损耗成本计算",
    )
    estimated_loss_amount = fields.Float(
        string="估计损失金额 (元)",
        digits=(18, 2),
        help="金价 × 重量 + 工时费",
    )
    # 关联损失
    return_to_operation_id = fields.Many2one(
        "gold.process.operation",
        string="退回工序",
        help="返工/退回时指定的工序",
    )
    return_production_id = fields.Many2one(
        "mrp.production",
        string="关联重做订单",
        help="报废/返工时新建的关联订单",
    )
    # 关闭
    close_time = fields.Datetime(string="关闭时间")
    close_note = fields.Text(string="关闭说明")
    # 复合
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        default=lambda self: self.env.company,
    )
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("name_unique", "UNIQUE(name, company_id)", "NCR 编号必须唯一"),
    ]

    @api.model
    def create(self, vals):
        if vals.get("name", _("新 NCR")) == _("新 NCR"):
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("gold.ncr") or _("新 NCR")
            )
        return super().create(vals)

    # ============================================================
    # 动作
    # ============================================================

    def action_rework(self, return_to_operation_id=None, note=None):
        """返工"""
        for rec in self:
            if rec.disposition not in ("pending", "return"):
                raise UserError(_("仅待处置 / 退回状态可发起返工 (当前: %s)") % rec.disposition)
            rec.write({
                "disposition": "rework",
                "disposition_time": fields.Datetime.now(),
                "disposition_by_id": self.env.user.id,
                "return_to_operation_id": return_to_operation_id,
                "disposition_note": note or "",
            })

    def action_concession(self, note=None, loss_amount=None):
        """让步放行(标次品降价)"""
        for rec in self:
            if rec.disposition != "pending":
                raise UserError(_("仅待处置状态可让步放行 (当前: %s)") % rec.disposition)
            rec.write({
                "disposition": "concession",
                "disposition_time": fields.Datetime.now(),
                "disposition_by_id": self.env.user.id,
                "disposition_note": note or "",
                "estimated_loss_amount": loss_amount or rec.estimated_loss_amount,
            })
            # 标记件为次品(继续流程)
            if rec.piece_id:
                rec.piece_id.write({"note": (rec.piece_id.note or "") + "\n[NCR让步] %s" % (note or "")})

    def action_scrap(self, note=None):
        """报废"""
        for rec in self:
            if rec.disposition not in ("pending", "rework"):
                raise UserError(_("仅待处置 / 返工状态可报废 (当前: %s)") % rec.disposition)
            rec.write({
                "disposition": "scrap",
                "disposition_time": fields.Datetime.now(),
                "disposition_by_id": self.env.user.id,
                "disposition_note": note or "",
            })
            # 件标记报废
            if rec.piece_id:
                rec.piece_id.write({"state": "scrap"})

    def action_return(self, return_to_operation_id=None, note=None):
        """退回上工序"""
        for rec in self:
            if rec.disposition != "pending":
                raise UserError(_("仅待处置状态可退回 (当前: %s)") % rec.disposition)
            rec.write({
                "disposition": "return",
                "disposition_time": fields.Datetime.now(),
                "disposition_by_id": self.env.user.id,
                "return_to_operation_id": return_to_operation_id,
                "disposition_note": note or "",
            })

    def action_close(self, note=None):
        """关闭 NCR"""
        for rec in self:
            if rec.disposition in ("pending",):
                raise UserError(_("待处置状态不能关闭,需先选定处置"))
            rec.write({
                "disposition": "closed",
                "close_time": fields.Datetime.now(),
                "close_note": note or "",
            })

    # ============================================================
    # 自动建 NCR(从源头触发)
    # ============================================================

    @api.model
    def auto_create_from_report(self, report_id):
        """从工序报工 quality_state=failed 自动建 NCR"""
        report = self.env["gold.workorder.report"].browse(report_id)
        if not report.exists():
            return False
        if report.quality_state != "failed":
            return False
        ncr = self.create({
            "source": "workorder_report",
            "source_model": "gold.workorder.report",
            "source_id": report.id,
            "workorder_report_id": report.id,
            "production_id": report.production_id.id,
            "piece_id": report.piece_id.id if hasattr(report, 'piece_id') and report.piece_id else None,
            "defect_type": "工序不合格",
            "defect_description": report.defect_description or "工序报工标记为不合格",
            "defect_weight_g": report.output_weight_g,
        })
        return ncr

    # ============================================================
    # 追溯查询
    # ============================================================

    @api.model
    def get_ncr_dashboard(self, days=7):
        """NCR 看板数据"""
        from datetime import timedelta
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), days=days)
        ncrs = self.search([("ncr_time", ">=", cutoff)])
        by_disp = {}
        for n in ncrs:
            d = n.disposition
            by_disp[d] = by_disp.get(d, 0) + 1
        return {
            "total": len(ncrs),
            "by_disposition": by_disp,
            "pending_count": len(ncrs.filtered(lambda n: n.disposition == "pending")),
            "total_loss_amount": sum(ncrs.mapped("estimated_loss_amount")),
        }