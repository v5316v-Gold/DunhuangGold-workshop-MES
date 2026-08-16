# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 工单扩展(mrp.workorder)
========================================

工单 = 生产订单 + 工序 + 工位 + 计划工时 + 损耗定额
"""

from odoo import models, fields, api


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    gold_process_operation_id = fields.Many2one(
        "gold.process.operation",
        string="工艺工序",
        related="operation_id",
        help="车间工艺工序字典",
    )
    gold_workstation_id = fields.Many2one(
        "gold.workstation",
        string="车间工位",
    )
    gold_standard_time_hours = fields.Float(
        string="标准工时 (h)",
        digits=(10, 4),
    )
    gold_standard_loss_rate = fields.Float(
        string="标准损耗率 (%)",
        digits=(6, 4),
    )
    gold_report_ids = fields.One2many(
        "gold.workorder.report",
        "workorder_id",
        string="工序报工记录",
    )
    gold_report_count = fields.Integer(
        string="报工次数",
        compute="_compute_gold_report_count",
        store=True,
    )

    @api.depends("gold_report_ids")
    def _compute_gold_report_count(self):
        for rec in self:
            rec.gold_report_count = len(rec.gold_report_ids)

    @api.onchange("operation_id")
    def _onchange_op(self):
        if self.operation_id:
            self.gold_process_operation_id = self.operation_id
