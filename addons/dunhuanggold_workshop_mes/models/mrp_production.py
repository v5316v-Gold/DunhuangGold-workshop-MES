# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 生产订单扩展
==============================

继承 mrp.production,扩展:
  - 工艺归属 (油压 / 失蜡)
  - 关联工艺路线 (gold.process.route)
  - 关联铸造模具 / 蜡模
  - 客户订单号(从下游接收)
  - 金价锁价
  - 当前工序 / 工位
  - 累计损耗 / 状态
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    # 贵金属专属
    gold_process_type = fields.Selection(
        [
            ("oil_press", "油压"),
            ("lost_wax", "失蜡"),
        ],
        string="工艺归属",
        related="product_id.gold_process_type",
        store=True,
    )
    gold_route_id = fields.Many2one(
        "gold.process.route",
        string="工艺路线",
        help="车间工艺路线模板",
    )
    gold_mold_id = fields.Many2one(
        "gold.mold",
        string="油压模具",
        help="油压工艺的模具",
    )
    gold_wax_model_id = fields.Many2one(
        "gold.wax.model",
        string="蜡模",
        help="失蜡工艺的蜡模",
    )
    gold_customer_order_no = fields.Char(
        string="客户订单号",
        help="从下游接收的订单号",
    )
    gold_locked_price = fields.Float(
        string="锁价 (元/g)",
        digits=(18, 4),
        default=0.0,
        help="订单报价时锁定的金价,用于成本核算",
    )
    gold_locked_until = fields.Datetime(
        string="锁价过期",
    )
    # 重量
    gold_planned_weight_g = fields.Float(
        string="计划金料 (g)",
        digits=(18, 6),
        default=0.0,
        help="按工艺路线总损耗率计算",
    )
    gold_actual_weight_g = fields.Float(
        string="实际金料 (g)",
        digits=(18, 6),
        default=0.0,
    )
    gold_actual_cast_weight_g = fields.Float(
        string="实际铸件 (g)",
        digits=(18, 6),
        default=0.0,
    )
    gold_actual_loss_g = fields.Float(
        string="实际损耗 (g)",
        digits=(18, 6),
        compute="_compute_actual_loss",
        store=True,
    )
    gold_actual_loss_rate = fields.Float(
        string="实际损耗率 (%)",
        digits=(6, 4),
        compute="_compute_actual_loss",
        store=True,
    )
    gold_planned_loss_rate = fields.Float(
        string="计划损耗率 (%)",
        digits=(6, 4),
        related="gold_route_id.total_loss_rate",
        store=True,
    )
    gold_loss_diff_pct = fields.Float(
        string="损耗率偏差 (%)",
        digits=(6, 4),
        compute="_compute_actual_loss",
        store=True,
        help="实际 - 计划,超过阈值预警",
    )
    # 状态
    gold_state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("received", "已接收"),  # Phase 3.1: 车间班长接收
            ("in_progress", "进行中"),
            ("to_close", "待关闭"),
            ("done", "已完成"),
            ("cancelled", "已取消"),
        ],
        string="车间状态",
        default="draft",
        tracking=True,
    )
    # Phase 3.1: 任务单接收记录
    received_at = fields.Datetime(
        string="接收时间",
        readonly=True,
    )
    received_by_id = fields.Many2one(
        "res.users",
        string="接收人(班组长)",
        readonly=True,
    )
    reception_note = fields.Text(
        string="接收备注",
        readonly=True,
    )
    gold_current_operation_id = fields.Many2one(
        "gold.process.operation",
        string="当前工序",
    )
    gold_current_workstation_id = fields.Many2one(
        "gold.workstation",
        string="当前工位",
    )
    gold_report_count = fields.Integer(
        string="工序报工数",
        compute="_compute_gold_stats",
        store=True,
    )
    gold_quality_check_count = fields.Integer(
        string="质检点数",
        compute="_compute_gold_stats",
        store=True,
    )
    gold_total_input_g = fields.Float(
        string="总投料 (g)",
        digits=(18, 6),
        compute="_compute_gold_stats",
        store=True,
    )
    gold_total_output_g = fields.Float(
        string="总产出 (g)",
        digits=(18, 6),
        compute="_compute_gold_stats",
        store=True,
    )

    @api.depends("gold_actual_weight_g", "gold_actual_cast_weight_g")
    def _compute_actual_loss(self):
        for rec in self:
            if rec.gold_actual_weight_g > 0:
                rec.gold_actual_loss_g = rec.gold_actual_weight_g - rec.gold_actual_cast_weight_g
                rec.gold_actual_loss_rate = (rec.gold_actual_loss_g / rec.gold_actual_weight_g) * 100
                rec.gold_loss_diff_pct = rec.gold_actual_loss_rate - (rec.gold_planned_loss_rate or 0.0)
            else:
                rec.gold_actual_loss_g = 0.0
                rec.gold_actual_loss_rate = 0.0
                rec.gold_loss_diff_pct = 0.0

    @api.depends("workorder_ids")
    def _compute_gold_stats(self):
        for rec in self:
            reports = self.env["gold.workorder.report"].search([("production_id", "=", rec.id)])
            rec.gold_report_count = len(reports)
            rec.gold_quality_check_count = len(reports.filtered("operation_id.need_quality_check"))
            rec.gold_total_input_g = sum(reports.mapped("input_weight_g"))
            rec.gold_total_output_g = sum(reports.mapped("output_weight_g"))

    @api.onchange("product_id")
    def _onchange_product_id_route(self):
        if self.product_id and self.product_id.gold_route_id:
            self.gold_route_id = self.product_id.gold_route_id

    def action_confirm(self):
        """确认 → 锁定工艺路线,生成工单"""
        for rec in self:
            if not rec.gold_route_id:
                raise UserError(_("生产订单 %s 缺少工艺路线") % rec.name)
            if rec.product_qty and rec.gold_route_id.total_loss_rate:
                # 计划金料 = 实际成品 × (1 + 损耗率)
                # 这里通过 BOM 单件重量 × (1 + 损耗率)
                standard_weight = rec.product_id.gold_standard_weight_g or 0.0
                if not standard_weight:
                    # 用 BOM 计算
                    bom = rec.bom_id
                    if bom and bom.bom_line_ids:
                        for line in bom.bom_line_ids:
                            if line.product_id.categ_id.gold_metal_type in (
                                "fine_gold",
                                "k_gold",
                                "platinum",
                                "palladium",
                                "silver",
                            ):
                                standard_weight += line.product_qty
                if standard_weight:
                    rec.gold_planned_weight_g = standard_weight * (1 + rec.gold_route_id.total_loss_rate / 100.0)
            rec.gold_state = "confirmed"
        return super().action_confirm()

    def action_start(self):
        for rec in self:
            if rec.gold_state == "received":
                rec.gold_state = "in_progress"
            else:
                rec.gold_state = "in_progress"

    def action_receive(self, user_id=None, note=None):
        """Phase 3.1: 车间班组长接收任务单。

        接收前自动校验:
          1. 工艺路线已指定
          2. 计划金料已计算
          3. (软校验) 模具 / 设备 / 人员 — 仅警告不阻断
        """
        for rec in self:
            if rec.gold_state != "confirmed":
                raise UserError(_("仅已确认订单可被接收 (当前: %s)") % rec.gold_state)
            if not rec.gold_route_id:
                raise UserError(_("订单 %s 缺少工艺路线,无法接收") % rec.name)
            if rec.gold_planned_weight_g <= 0:
                raise UserError(_("订单 %s 计划金料未计算,无法接收") % rec.name)
            rec.write({
                "gold_state": "received",
                "received_at": fields.Datetime.now(),
                "received_by_id": user_id or self.env.user.id,
                "reception_note": note or "",
            })
        return True

    def action_start_after_received(self):
        """Phase 3.1: 接收后开始第一道工序(由 workorder_report.create 隐式触发)"""
        for rec in self:
            if rec.gold_state == "received":
                rec.gold_state = "in_progress"

    def action_done(self):
        for rec in self:
            rec.gold_state = "done"

    def action_cancel(self):
        for rec in self:
            rec.gold_state = "cancelled"

    def action_apply_route(self):
        """应用工艺路线 → 生成工单"""
        self.ensure_one()
        if not self.gold_route_id:
            raise UserError(_("未指定工艺路线"))
        if self.workorder_ids:
            raise UserError(_("已有工单,不可重复应用"))
        # 删除原工单
        # 反向:从 process.route 复制 to mrp.workorder
        # 这里调用 mrp_production 的 _workorders_create
        # 简化:直接生成 workorder
        workorder_obj = self.env["mrp.workorder"]
        for i, line in enumerate(self.gold_route_id.operation_ids):
            workorder_obj.create({
                "name": "%s - %s" % (self.name, line.operation_id.name),
                "production_id": self.id,
                "operation_id": line.operation_id.id,
                "workcenter_id": self.env["mrp.workcenter"].search([], limit=1).id
                    if self.env["mrp.workcenter"].search([], limit=1)
                    else self._create_default_workcenter().id,
                "sequence": line.sequence,
                "gold_standard_time_hours": line.standard_time_hours,
                "gold_standard_loss_rate": line.standard_loss_rate,
                "gold_workstation_id": line.workstation_id.id,
            })
        return True

    def _create_default_workcenter(self):
        """创建默认工作中心"""
        return self.env["mrp.workcenter"].create({
            "name": "默认工位",
            "code": "DEFAULT-WC",
        })
