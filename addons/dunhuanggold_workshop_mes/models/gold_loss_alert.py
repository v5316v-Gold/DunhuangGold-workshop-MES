# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 损耗监控预警 (Phase 3.2 增强)
================================================

三层损耗监控:
  Layer 1. 工序级   每道报工 vs 工序定额
  Layer 2. 累积级   当前工序完成时 vs 工艺路线总定额
  Layer 3. 趋势级   同操作员/模具/设备 7/30 天趋势,3σ 检测

触发:
  - Layer 1: 工序报工 action_confirm 时自动检测
    - 偏差 > 20%: 黄色警告(单道)
    - 偏差 > 50% 或绝对值 > 1g: 红色(自动建 NCR)
  - Layer 2: 生产订单每完成一道,自动算累积损耗
    - 累积 > 路线定额: 红色(需班组长 review)
  - Layer 3: cron 每日 23:00 跑(后续)
    - 同维度 30 天标准差 > 3σ: 黄色
    - 7 天趋势 vs 30 天均值 > +50%: 红色

状态机:
  open → acknowledged → resolved
       → ignored(误报)
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


ALERT_TYPE = [
    ("operation", "工序级"),     # Layer 1
    ("cumulative", "累积级"),   # Layer 2
    ("trend", "趋势级"),         # Layer 3
]

ALERT_SEVERITY = [
    ("info", "提示"),
    ("warning", "黄色警告"),
    ("danger", "红色报警"),
]

ALERT_STATUS = [
    ("open", "待处理"),
    ("acknowledged", "已确认"),
    ("resolved", "已解决"),
    ("ignored", "已忽略"),
]


class GoldLossAlert(models.Model):
    _name = "gold.loss.alert"
    _description = "损耗监控预警"
    _order = "triggered_at desc, severity, id"
    _rec_name = "display_name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    display_name = fields.Char(string="描述", compute="_compute_display_name", store=True)

    alert_type = fields.Selection(
        ALERT_TYPE,
        string="预警类型",
        required=True,
        index=True,
    )
    severity = fields.Selection(
        ALERT_SEVERITY,
        string="严重度",
        required=True,
        index=True,
    )
    status = fields.Selection(
        ALERT_STATUS,
        string="状态",
        default="open",
        required=True,
        tracking=True,
        index=True,
    )

    # 触发时间
    triggered_at = fields.Datetime(
        string="触发时间",
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    acknowledged_at = fields.Datetime(string="确认时间")
    acknowledged_by_id = fields.Many2one("res.users", string="确认人")
    resolved_at = fields.Datetime(string="解决时间")
    resolved_by_id = fields.Many2one("res.users", string="解决人")
    resolve_note = fields.Text(string="解决说明")

    # 关联
    workorder_report_id = fields.Many2one(
        "gold.workorder.report", string="关联工序报工", index=True,
    )
    production_id = fields.Many2one(
        "mrp.production", string="生产订单", index=True,
    )
    piece_id = fields.Many2one("gold.piece", string="件级 SN")
    operation_id = fields.Many2one(
        "gold.process.operation", string="工序", index=True,
    )
    mold_id = fields.Many2one("gold.mold", string="模具", index=True)
    equipment_id = fields.Many2one(
        "gold.equipment", string="设备", index=True,
    )
    operator_id = fields.Many2one(
        "res.users", string="操作员", index=True,
    )

    # 数值
    actual_loss_g = fields.Float(
        string="实际损耗 (g)",
        digits=(18, 6),
    )
    expected_loss_g = fields.Float(
        string="定额损耗 (g)",
        digits=(18, 6),
    )
    deviation_g = fields.Float(
        string="偏差 (g)",
        digits=(18, 6),
        compute="_compute_deviation",
        store=True,
    )
    actual_loss_rate = fields.Float(
        string="实际损耗率 (%)",
        digits=(6, 4),
    )
    expected_loss_rate = fields.Float(
        string="定额损耗率 (%)",
        digits=(6, 4),
    )
    deviation_pct = fields.Float(
        string="偏差 (%)",
        digits=(6, 4),
        compute="_compute_deviation",
        store=True,
    )

    # 累积/趋势
    cumulative_loss_g = fields.Float(
        string="累积损耗 (g)",
        digits=(18, 6),
        help="到当前工序的累计损耗",
    )
    cumulative_standard_g = fields.Float(
        string="累积定额 (g)",
        digits=(18, 6),
    )

    # 统计 (Layer 3)
    baseline_avg = fields.Float(
        string="基线均值",
        digits=(6, 4),
        help="同维度 30 天历史均值",
    )
    baseline_std = fields.Float(
        string="基线标准差",
        digits=(6, 4),
    )
    z_score = fields.Float(
        string="Z-Score",
        digits=(6, 2),
    )

    # 描述
    description = fields.Text(string="预警描述", compute="_compute_description", store=True)
    suggestion = fields.Text(
        string="建议措施",
        help="自动生成的处置建议(操作员/设备/模具检查等)",
    )

    # 复合
    company_id = fields.Many2one(
        "res.company", string="公司", default=lambda self: self.env.company,
    )

    _sql_constraints = [
        ("name_unique", "UNIQUE(display_name, company_id)", "预警描述必须唯一"),
    ]

    @api.depends("alert_type", "operation_id", "operator_id", "mold_id", "equipment_id")
    def _compute_display_name(self):
        for rec in self:
            parts = []
            if rec.operation_id:
                parts.append(rec.operation_id.name)
            if rec.alert_type == "trend":
                if rec.operator_id:
                    parts.append(f"操作员 {rec.operator_id.name}")
                if rec.mold_id:
                    parts.append(f"模具 {rec.mold_id.name}")
                if rec.equipment_id:
                    parts.append(f"设备 {rec.equipment_id.name}")
            type_label = dict(ALERT_TYPE).get(rec.alert_type, "")
            parts.append(type_label)
            rec.display_name = " / ".join(filter(None, parts)) or f"#{rec.id}"

    @api.depends("actual_loss_g", "expected_loss_g", "actual_loss_rate", "expected_loss_rate")
    def _compute_deviation(self):
        for rec in self:
            rec.deviation_g = rec.actual_loss_g - rec.expected_loss_g
            rec.deviation_pct = rec.actual_loss_rate - rec.expected_loss_rate

    @api.depends("alert_type", "severity", "deviation_pct", "z_score", "operator_id", "mold_id")
    def _compute_description(self):
        for rec in self:
            desc_parts = []
            if rec.alert_type == "operation":
                desc_parts.append(
                    f"工序 {rec.operation_id.name or '?'} 损耗 {rec.actual_loss_rate:.2f}% "
                    f"(定额 {rec.expected_loss_rate:.2f}%, 偏差 {rec.deviation_pct:+.2f}%)"
                )
            elif rec.alert_type == "cumulative":
                desc_parts.append(
                    f"生产订单 {rec.production_id.name or '?'} 累积损耗 {rec.cumulative_loss_g:.3f}g "
                    f"超定额 {rec.cumulative_standard_g:.3f}g"
                )
            elif rec.alert_type == "trend":
                if rec.z_score:
                    desc_parts.append(
                        f"Z-Score = {rec.z_score:.2f} (超过 3σ 阈值)"
                    )
                else:
                    desc_parts.append("趋势异常")
            if rec.severity == "danger":
                desc_parts.append("🔴 严重")
            elif rec.severity == "warning":
                desc_parts.append("🟡 警告")
            rec.description = " | ".join(desc_parts)

    # ============================================================
    # 动作
    # ============================================================

    def action_acknowledge(self):
        """班组长确认收到预警"""
        for rec in self:
            if rec.status != "open":
                raise UserError(_("仅待处理状态可确认 (当前: %s)") % rec.status)
            rec.write({
                "status": "acknowledged",
                "acknowledged_at": fields.Datetime.now(),
                "acknowledged_by_id": self.env.user.id,
            })

    def action_resolve(self, note=None):
        """解决预警"""
        for rec in self:
            if rec.status not in ("open", "acknowledged"):
                raise UserError(_("仅待处理 / 已确认状态可解决 (当前: %s)") % rec.status)
            rec.write({
                "status": "resolved",
                "resolved_at": fields.Datetime.now(),
                "resolved_by_id": self.env.user.id,
                "resolve_note": note or "",
            })

    def action_ignore(self, note=None):
        """忽略预警(误报)"""
        for rec in self:
            if rec.status not in ("open", "acknowledged"):
                raise UserError(_("仅待处理 / 已确认状态可忽略 (当前: %s)") % rec.status)
            rec.write({
                "status": "ignored",
                "resolved_at": fields.Datetime.now(),
                "resolved_by_id": self.env.user.id,
                "resolve_note": (rec.resolve_note or "") + f"\n[忽略] {note or ''}",
            })

    # ============================================================
    # 自动创建预警 (供各 Layer 调用)
    # ============================================================

    @api.model
    def _auto_check_operation_loss(self, report):
        """Layer 1: 工序报工完成时检查
        - 偏差 > 20%: 黄色
        - 偏差 > 50% 或 绝对偏差 > 1g: 红色
        """
        if not report or not report.standard_loss_rate:
            return False
        deviation = report.loss_diff_pct or 0
        actual = report.loss_g or 0
        abs_dev = abs(deviation)
        if abs_dev <= 20.0 and abs(actual) <= 1.0:
            return False  # 正常,无需预警

        severity = "danger" if abs_dev > 50.0 or abs(actual) > 1.0 else "warning"

        alert = self.create({
            "alert_type": "operation",
            "severity": severity,
            "workorder_report_id": report.id,
            "production_id": report.production_id.id,
            "operation_id": report.operation_id.id,
            "operator_id": report.operator_id.id,
            "equipment_id": report.equipment_id.id if report.equipment_id else None,
            "actual_loss_g": report.loss_g,
            "expected_loss_g": (report.input_weight_g or 0) * (report.standard_loss_rate / 100.0),
            "actual_loss_rate": report.loss_rate,
            "expected_loss_rate": report.standard_loss_rate,
            "suggestion": _(
                "建议检查: 1) 操作员资质 2) 设备精度 3) 模具磨损"
            ),
        })
        return alert

    @api.model
    def _auto_check_cumulative_loss(self, production, new_loss_g):
        """Layer 2: 累积损耗检查
        - 当前累积 > 路线总定额: 红色
        """
        if not production or not production.gold_route_id:
            return False
        standard_weight = production.gold_planned_weight_g or 0
        actual_weight = production.gold_actual_weight_g or 0
        if standard_weight <= 0 or actual_weight <= 0:
            return False
        # 累积损耗 / 计划重量
        cum_rate = (new_loss_g / standard_weight) * 100
        standard_rate = production.gold_planned_loss_rate or 0
        if cum_rate <= standard_rate * 1.2:  # 超出定额 20% 才预警
            return False
        return self.create({
            "alert_type": "cumulative",
            "severity": "danger",
            "production_id": production.id,
            "cumulative_loss_g": new_loss_g,
            "cumulative_standard_g": standard_weight,
            "actual_loss_rate": cum_rate,
            "expected_loss_rate": standard_rate,
            "suggestion": _(
                "订单总损耗超定额,需班组长/主任 review 工艺与每道工序"
            ),
        })

    @api.model
    def _auto_check_trend(self, dimension, target_id, days=30, current_loss_rate=0):
        """Layer 3: 趋势分析
        - 拿过去 30 天同维度的损耗率
        - 算 mean / std
        - 当前 vs baseline: z_score > 3 → 黄色警告
        """
        domain = [
            ("triggered_at", ">=", fields.Date.subtract(fields.Date.today(), days)),
        ]
        if dimension == "operator":
            domain.append(("operator_id", "=", target_id))
        elif dimension == "mold":
            domain.append(("mold_id", "=", target_id))
        elif dimension == "equipment":
            domain.append(("equipment_id", "=", target_id))
        alerts = self.search(domain)
        rates = [a.actual_loss_rate for a in alerts if a.actual_loss_rate]
        if len(rates) < 5:
            return False  # 数据不足
        mean = sum(rates) / len(rates)
        variance = sum((r - mean) ** 2 for r in rates) / len(rates)
        std = variance ** 0.5
        if std == 0:
            return False
        z = (current_loss_rate - mean) / std
        if z <= 3.0:
            return False
        severity = "danger" if z > 5.0 else "warning"
        vals = {
            "alert_type": "trend",
            "severity": severity,
            "actual_loss_rate": current_loss_rate,
            "baseline_avg": mean,
            "baseline_std": std,
            "z_score": z,
            "suggestion": _(
                "该维度 %s 过去 %d 天平均 %.2f%% 标准差 %.2f, 当前 %.2f%% 偏离 Z=%.2f"
            ) % (dimension, days, mean, std, current_loss_rate, z),
        }
        if dimension == "operator":
            vals["operator_id"] = target_id
        elif dimension == "mold":
            vals["mold_id"] = target_id
        elif dimension == "equipment":
            vals["equipment_id"] = target_id
        return self.create(vals)

    # ============================================================
    # 看板查询
    # ============================================================

    @api.model
    def get_dashboard(self, days=7):
        """损耗预警看板数据"""
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), days=days)
        alerts = self.search([("triggered_at", ">=", cutoff)])
        by_type = {}
        by_severity = {}
        for a in alerts:
            by_type[a.alert_type] = by_type.get(a.alert_type, 0) + 1
            by_severity[a.severity] = by_severity.get(a.severity, 0) + 1
        open_alerts = alerts.filtered(lambda a: a.status == "open")
        resolved = alerts.filtered(lambda a: a.status == "resolved")
        return {
            "total": len(alerts),
            "open_count": len(open_alerts),
            "resolved_count": len(resolved),
            "by_type": by_type,
            "by_severity": by_severity,
            "open_recent": [{
                "id": a.id,
                "name": a.display_name,
                "type": a.alert_type,
                "severity": a.severity,
                "operation": a.operation_id.name if a.operation_id else None,
                "operator": a.operator_id.name if a.operator_id else None,
                "deviation_pct": a.deviation_pct,
                "triggered_at": str(a.triggered_at),
                "description": a.description,
            } for a in open_alerts[:10]],
        }