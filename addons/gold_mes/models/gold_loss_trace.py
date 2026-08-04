# -*- coding: utf-8 -*-
"""
贵金属车间 ERP — 损耗追溯
============================

按生产订单汇总工序级损耗,生成损耗追溯记录:
  - 工序损耗明细
  - 与定额对比
  - 异常标记
  - 复盘记录
"""

from odoo import models, fields, api, _


class GoldLossTrace(models.Model):
    _name = "gold.loss.trace"
    _description = "损耗追溯"
    _order = "trace_time desc, id desc"
    _rec_name = "name"

    name = fields.Char(
        string="追溯单号",
        required=True,
        readonly=True,
        default=lambda self: _("新追溯"),
    )
    production_id = fields.Many2one(
        "mrp.production",
        string="生产订单",
        required=True,
    )
    operation_id = fields.Many2one(
        "gold.process.operation",
        string="工序",
        required=True,
    )
    workorder_id = fields.Many2one(
        "mrp.workorder",
        string="工单",
    )
    report_id = fields.Many2one(
        "gold.workorder.report",
        string="报工单",
    )
    input_weight_g = fields.Float(
        string="投料 (g)",
        digits=(18, 6),
        required=True,
    )
    output_weight_g = fields.Float(
        string="产出 (g)",
        digits=(18, 6),
        required=True,
    )
    loss_g = fields.Float(
        string="损耗 (g)",
        digits=(18, 6),
        required=True,
    )
    loss_rate = fields.Float(
        string="损耗率 (%)",
        digits=(6, 4),
        required=True,
    )
    standard_loss_rate = fields.Float(
        string="定额损耗率 (%)",
        digits=(6, 4),
    )
    loss_diff_pct = fields.Float(
        string="损耗偏差 (%)",
        digits=(6, 4),
    )
    is_over_loss = fields.Boolean(
        string="是否超耗",
    )
    review_status = fields.Selection(
        [
            ("pending", "待复盘"),
            ("in_progress", "复盘中"),
            ("resolved", "已处理"),
            ("ignored", "已忽略"),
        ],
        string="复盘状态",
        default="pending",
    )
    review_note = fields.Text(string="复盘结论")
    trace_time = fields.Datetime(
        string="追溯时间",
        default=fields.Datetime.now,
    )
    reviewer_id = fields.Many2one(
        "res.users",
        string="复盘人",
    )
    note = fields.Text(string="备注")

    @api.model
    def create_from_report(self, report_id):
        """从报工单生成追溯"""
        report = self.env["gold.workorder.report"].browse(report_id)
        if not report.exists():
            return False
        trace = self.create({
            "production_id": report.production_id.id,
            "operation_id": report.operation_id.id,
            "workorder_id": report.workorder_id.id,
            "report_id": report.id,
            "input_weight_g": report.input_weight_g,
            "output_weight_g": report.output_weight_g,
            "loss_g": report.loss_g,
            "loss_rate": report.loss_rate,
            "standard_loss_rate": report.standard_loss_rate,
            "loss_diff_pct": report.loss_diff_pct,
            "is_over_loss": report.is_over_loss,
        })
        if trace.is_over_loss:
            trace.review_status = "pending"
        else:
            trace.review_status = "ignored"
        return trace
