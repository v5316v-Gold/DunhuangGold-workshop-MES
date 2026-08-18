# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 工序报工
==========================

每完成一道工序,生成一条报工记录:
  - 报工单号: BG + YYYYMMDD + XXX
  - 关联: 生产订单 + 工单 + 工序 + 工位 + 操作员
  - 投料重量(g) : 电子天平直采
  - 产出重量(g) : 电子天平直采
  - 工时(h) : 自动累计或手工
  - 损耗量 = 投料 - 产出
  - 损耗率 = 损耗 / 投料 × 100%
  - 损耗率偏差 = 实际 - 工序定额
  - 质量判定:
    - 合格 / 不合格 / 返工
  - 异常标记: > 阈值 (默认 20%)

投入物料: 一个工序可消耗多个批次金料
产出物料: 蜡模 / 半成品 / 铸件
"""

import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


REPORT_QUALITY_SELECTION = [
    ("passed", "合格"),
    ("failed", "不合格"),
    ("rework", "返工"),
    ("scrap", "报废"),
]


SOURCE_SELECTION = [
    ("manual", "手工录入"),
    ("balance", "电子天平直采"),
    ("plc", "PLC / 设备"),
    ("opc_ua", "OPC UA"),
    ("mqtt", "MQTT"),
    ("rest_api", "REST API"),
]


class GoldWorkorderReport(models.Model):
    _name = "gold.workorder.report"
    _description = "工序报工"
    _order = "report_time desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"

    name = fields.Char(
        string="报工单号",
        required=True,
        readonly=True,
        default=lambda self: _("新报工"),
    )
    # 关联
    production_id = fields.Many2one(
        "mrp.production",
        string="生产订单",
        required=True,
        index=True,
        ondelete="cascade",
    )
    workorder_id = fields.Many2one(
        "mrp.workorder",
        string="工单",
        index=True,
        ondelete="cascade",
    )
    operation_id = fields.Many2one(
        "gold.process.operation",
        string="工序",
        required=True,
        index=True,
    )
    workstation_id = fields.Many2one(
        "gold.workstation",
        string="工位",
        index=True,
    )
    equipment_id = fields.Many2one(
        "gold.equipment",
        string="设备",
        index=True,
    )
    # 人员
    operator_id = fields.Many2one(
        "res.users",
        string="操作员",
        required=True,
        index=True,
    )
    inspector_id = fields.Many2one(
        "res.users",
        string="检验员",
    )
    # 投入物料
    input_batch_id = fields.Many2one(
        "gold.material.batch",
        string="投料批次",
    )
    input_weight_g = fields.Float(
        string="投料重量 (g)",
        digits=(18, 6),
        required=True,
        default=0.0,
    )
    # 产出物料
    output_weight_g = fields.Float(
        string="产出重量 (g)",
        digits=(18, 6),
        required=True,
        default=0.0,
    )
    output_batch_id = fields.Many2one(
        "gold.material.batch",
        string="产出批次",
        help="半成品入库,失蜡为铸件,油压为冲切件",
    )
    output_piece_count = fields.Integer(
        string="产出件数",
        default=1,
    )
    # 损耗
    loss_g = fields.Float(
        string="损耗量 (g)",
        digits=(18, 6),
        compute="_compute_loss",
        store=True,
    )
    loss_rate = fields.Float(
        string="损耗率 (%)",
        digits=(6, 4),
        compute="_compute_loss",
        store=True,
    )
    standard_loss_rate = fields.Float(
        string="工序定额损耗 (%)",
        digits=(6, 4),
    )
    loss_diff_pct = fields.Float(
        string="损耗差异 (%)",
        digits=(6, 4),
        compute="_compute_loss",
        store=True,
        help="实际-定额,绝对值 > 阈值预警",
    )
    is_over_loss = fields.Boolean(
        string="超耗预警",
        compute="_compute_loss",
        store=True,
    )
    # 工时
    work_hours = fields.Float(
        string="工时 (h)",
        digits=(10, 4),
        required=True,
        default=0.0,
    )
    standard_work_hours = fields.Float(
        string="定额工时 (h)",
        digits=(10, 4),
    )
    time_diff = fields.Float(
        string="工时差异 (h)",
        digits=(10, 4),
        compute="_compute_time_diff",
        store=True,
    )
    # 质量
    quality_state = fields.Selection(
        REPORT_QUALITY_SELECTION,
        string="质量判定",
        default="passed",
        required=True,
    )
    defect_description = fields.Text(
        string="缺陷描述",
    )
    # 时间
    report_time = fields.Datetime(
        string="报工时间",
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    start_time = fields.Datetime(string="开始时间")
    end_time = fields.Datetime(string="结束时间")
    # 数据来源
    source = fields.Selection(
        SOURCE_SELECTION,
        string="采集来源",
        default="manual",
        required=True,
    )
    balance_id = fields.Many2one(
        "gold.equipment",
        string="使用的天平",
        domain=[("category", "=", "balance")],
    )
    # 损耗回收
    recyclable_wax_g = fields.Float(
        string="回收蜡 (g)",
        digits=(18, 6),
        default=0.0,
    )
    recyclable_gold_g = fields.Float(
        string="回收金(浇口) (g)",
        digits=(18, 6),
        default=0.0,
    )
    # 状态
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("cancelled", "取消"),
        ],
        string="状态",
        default="draft",
        required=True,
        tracking=True,
        help="草稿态可改;确认后触发批次消耗/生产订单启动/模具累计;"
             "取消后不回退批次消耗(避免双花)",
    )
    note = fields.Text(string="备注")

    _sql_constraints = [
        (
            "input_positive",
            "CHECK(input_weight_g >= 0)",
            "投料重量必须 ≥ 0",
        ),
        (
            "output_positive",
            "CHECK(output_weight_g >= 0)",
            "产出重量必须 ≥ 0",
        ),
    ]

    @api.depends("input_weight_g", "output_weight_g", "standard_loss_rate")
    def _compute_loss(self):
        for rec in self:
            rec.loss_g = max(0.0, rec.input_weight_g - rec.output_weight_g)
            if rec.input_weight_g > 0:
                rec.loss_rate = (rec.loss_g / rec.input_weight_g) * 100
            else:
                rec.loss_rate = 0.0
            rec.loss_diff_pct = rec.loss_rate - (rec.standard_loss_rate or 0.0)
            tolerance = self.env.company.gold_loss_tolerance_pct or 20.0
            rec.is_over_loss = abs(rec.loss_diff_pct) > tolerance

    @api.depends("work_hours", "standard_work_hours")
    def _compute_time_diff(self):
        for rec in self:
            rec.time_diff = rec.work_hours - (rec.standard_work_hours or 0.0)

    @api.model
    def create(self, vals):
        """创建报工记录(草稿态)。

        仅做自动填充,不触发任何业务副作用。
        业务副作用(批次消耗 / 生产订单启动 / 模具累计)统一在
        :meth:`action_confirm` 中触发,保证:
          - 草稿态可反复修改 input/output weight
          - 只有显式确认后才扣减金料,避免误操作双花
        """
        if vals.get("name", _("新报工")) == _("新报工"):
            vals["name"] = self.env["ir.sequence"].next_by_code("gold.workorder.report")
        # 自动拉取工单的标准值
        if vals.get("workorder_id") and not vals.get("standard_loss_rate"):
            wo = self.env["mrp.workorder"].browse(vals["workorder_id"])
            if wo.gold_standard_loss_rate:
                vals["standard_loss_rate"] = wo.gold_standard_loss_rate
            if wo.gold_standard_time_hours and not vals.get("standard_work_hours"):
                vals["standard_work_hours"] = wo.gold_standard_time_hours
        return super().create(vals)

    def action_confirm(self):
        """确认报工,触发批次消耗 / 生产订单启动 / 模具累计。

        仅草稿态可确认。已确认后所有业务副作用已发生,不可回退
        (如需修改,使用 action_cancel 标记作废后重报)。
        """
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("报工 %s 仅草稿态可确认 (当前: %s)") % (rec.name, rec.state))
            # 1. 批次消耗(若报工指定了 input_batch)
            if rec.input_batch_id:
                rec.input_batch_id.consume(rec.input_weight_g)
            # 2. 生产订单进入 in_progress(若仍处 confirmed)
            if rec.production_id and rec.production_id.gold_state == "confirmed":
                rec.production_id.action_start()
            # 3. 模具累计使用
            if rec.production_id and rec.production_id.gold_mold_id:
                rec.production_id.gold_mold_id.action_add_usage(rec.output_piece_count)
            rec.state = "confirmed"
            # Phase 3.2: 工序级损耗监控 (Layer 1)
            # 自动检测偏差 > 20% / > 50% 触发预警
            if rec.production_id and rec.operation_id:
                self.env["gold.loss.alert"]._auto_check_operation_loss(rec)
                # Phase 3.2: 累积损耗监控 (Layer 2)
                if rec.production_id.gold_planned_weight_g:
                    new_cum_loss = (rec.production_id.gold_actual_loss_g or 0)
                    self.env["gold.loss.alert"]._auto_check_cumulative_loss(
                        rec.production_id, new_cum_loss
                    )

    def action_cancel(self):
        """作废报工。

        注意:已确认报工作废**不回退**批次消耗 / 生产订单状态 /
        模具累计 —— 业务上一旦报工即视为实物已发生,后续需通过
        补报/退料单走反向流程(后续版本实现)。
        """
        for rec in self:
            if rec.state == "confirmed":
                _logger.warning(
                    "报工 %s 已确认后取消, 不回退批次消耗/生产订单/模具",
                    rec.name,
                )
            rec.state = "cancelled"

    @api.constrains("operation_id", "workorder_id")
    def _check_operation_match(self):
        for rec in self:
            if rec.workorder_id and rec.workorder_id.operation_id and rec.operation_id != rec.workorder_id.operation_id:
                raise ValidationError(_("报工工序与工单工序不一致"))

    def name_get(self):
        result = []
        for rec in self:
            display = f"[{rec.name}] {rec.operation_id.name} {rec.input_weight_g:.3f}→{rec.output_weight_g:.3f}g"
            result.append((rec.id, display))
        return result
