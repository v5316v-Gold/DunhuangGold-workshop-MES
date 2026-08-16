# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 看板数据
==============================

提供看板所需 KPI 聚合数据,看板页面 (QWeb) 调用。
"""

from odoo import models, fields, api, _


class GoldDashboard(models.Model):
    _name = "gold.dashboard"
    _description = "车间看板 KPI"
    _auto = False  # 纯计算视图,无表

    name = fields.Char(string="名称", default="车间看板")

    def name_get(self):
        return [(rec.id, "车间看板") for rec in self]

    @api.model
    def get_kpi(self):
        """聚合看板数据"""
        Process = self.env["mrp.production"]
        Report = self.env["gold.workorder.report"]
        Batch = self.env["gold.material.batch"]
        Mold = self.env["gold.mold"]
        Xrf = self.env["gold.xrf.record"]
        Today = fields.Date.context_today(self)

        # 当日完工
        done_today = Process.search([
            ("gold_state", "=", "done"),
            ("date_finished", ">=", Today),
        ])
        in_progress = Process.search([("gold_state", "=", "in_progress")])
        over_loss = Report.search([
            ("is_over_loss", "=", True),
            ("report_time", ">=", Today),
        ])
        done_count = len(done_today)
        in_progress_count = len(in_progress)
        over_loss_count = len(over_loss)

        # 模具预警
        molds = Mold.search([("state", "!=", "scrapped")])
        critical_molds = molds.filtered(
            lambda m: m.remaining_count <= m.rated_life_count * m.life_warning_pct / 100
        )

        # 工艺分布
        oil_press_orders = Process.search([
            ("gold_process_type", "=", "oil_press"),
            ("gold_state", "in", ["confirmed", "in_progress"]),
        ])
        lost_wax_orders = Process.search([
            ("gold_process_type", "=", "lost_wax"),
            ("gold_state", "in", ["confirmed", "in_progress"]),
        ])

        # 当前金价
        current_price = self.env["gold.price.engine"].get_current_price("au9999")

        # 库存估值
        batches = Batch.search([("state", "=", "available")])
        total_value = sum(batches.mapped("current_value"))

        # 平均损耗率
        recent_reports = Report.search(
            [("report_time", ">=", Today)],
            order="report_time desc",
            limit=100,
        )
        if recent_reports:
            avg_loss_rate = sum(recent_reports.mapped("loss_rate")) / len(recent_reports)
        else:
            avg_loss_rate = 0.0

        # XRF 检测合格率
        xrf_today = Xrf.search([("detection_time", ">=", Today)])
        xrf_passed = xrf_today.filtered("is_passed")
        xrf_pct = (len(xrf_passed) / len(xrf_today) * 100) if xrf_today else 0.0

        return {
            "today": str(Today),
            "done_today": done_count,
            "in_progress": in_progress_count,
            "over_loss_count": over_loss_count,
            "critical_mold_count": len(critical_molds),
            "oil_press_orders": len(oil_press_orders),
            "lost_wax_orders": len(lost_wax_orders),
            "current_gold_price": current_price,
            "total_value": total_value,
            "avg_loss_rate": avg_loss_rate,
            "xrf_count_today": len(xrf_today),
            "xrf_passed_pct": xrf_pct,
        }

    @api.model
    def get_loss_trend(self, days=7):
        """最近 N 天损耗趋势"""
        Report = self.env["gold.workorder.report"]
        from datetime import timedelta
        end = fields.Date.context_today(self)
        start = end - timedelta(days=days)
        reports = Report.search([
            ("report_time", ">=", start),
            ("report_time", "<=", end),
        ])
        # 按天分组
        from collections import defaultdict
        groups = defaultdict(list)
        for r in reports:
            d = r.report_time.date()
            groups[d].append(r)
        result = []
        for d in sorted(groups.keys()):
            rs = groups[d]
            avg = sum(rs.mapped("loss_rate")) / len(rs) if rs else 0.0
            over = sum(1 for r in rs if r.is_over_loss)
            result.append({
                "date": str(d),
                "avg_loss_rate": avg,
                "report_count": len(rs),
                "over_loss_count": over,
            })
        return result

    @api.model
    def get_equipment_status(self):
        """设备状态分布"""
        Equip = self.env["gold.equipment"]
        equips = Equip.search([("active", "=", True)])
        groups = {}
        for e in equips:
            groups.setdefault(e.state, 0)
            groups[e.state] += 1
        return groups
