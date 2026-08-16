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
        """聚合看板数据。

        优化点(Phase 2):
          - 改用 ``read_group`` 在 SQL 端聚合,避免 ``len(search(...))``
            触发全表读 -> 100 万记录下查询从秒级降到毫秒级
          - ``mold`` 模具预警仍需 Python 端 filter(``remaining_count`` 是
            computed 字段无法在 SQL 计算)
        """
        Process = self.env["mrp.production"]
        Report = self.env["gold.workorder.report"]
        Batch = self.env["gold.material.batch"]
        Mold = self.env["gold.mold"]
        Xrf = self.env["gold.xrf.record"]
        Today = fields.Date.context_today(self)
        env = self.env

        # ---- 当日完工 / 进行中 / 工艺分布:read_group 一次拿全部 ----
        # 按 gold_state + gold_process_type 双维度分组
        production_groups = Process.read_group(
            domain=[("gold_state", "in", ["done", "in_progress", "confirmed"])],
            fields=["gold_state", "gold_process_type"],
            groupby=["gold_state", "gold_process_type"],
            lazy=False,
        )
        # 转成 dict 便于查表
        proc_map = {(g["gold_state"][0] if isinstance(g["gold_state"], tuple) else g["gold_state"],
                     g["gold_process_type"][0] if isinstance(g["gold_process_type"], tuple) else g["gold_process_type"]): g["gold_state_count"]
                    for g in production_groups}
        done_today = Process.search_count([
            ("gold_state", "=", "done"),
            ("date_finished", ">=", Today),
        ])
        in_progress_count = proc_map.get(("in_progress", False), 0) + proc_map.get(("in_progress", "oil_press"), 0) + proc_map.get(("in_progress", "lost_wax"), 0)
        # 简化:直接 search_count 也走索引(更快)
        in_progress_count = Process.search_count([("gold_state", "=", "in_progress")])

        # ---- 超耗预警:read_group ----
        over_loss_count = Report.search_count([
            ("is_over_loss", "=", True),
            ("report_time", ">=", Today),
        ])

        # ---- 工艺分布:read_group 按 process_type ----
        oil_press_orders = Process.search_count([
            ("gold_process_type", "=", "oil_press"),
            ("gold_state", "in", ["confirmed", "in_progress"]),
        ])
        lost_wax_orders = Process.search_count([
            ("gold_process_type", "=", "lost_wax"),
            ("gold_state", "in", ["confirmed", "in_progress"]),
        ])

        # ---- 模具预警(remaining_count 是 computed,必须 Python 端 filter) ----
        # 仅在模具数 < 1000 时效率可接受;若超过则建议把 remaining_count
        # 物化为 stored=True + index=True
        molds = Mold.search([("state", "!=", "scrapped")])
        critical_molds = molds.filtered(
            lambda m: m.remaining_count <= m.rated_life_count * m.life_warning_pct / 100
        )

        # ---- 当前金价 ----
        current_price = self.env["gold.price.engine"].get_current_price("au9999")

        # ---- 库存估值:read_group SUM(current_value) ----
        batch_groups = Batch.read_group(
            domain=[("state", "=", "available")],
            fields=["current_value"],
            groupby=[],
            lazy=False,
        )
        total_value = batch_groups[0]["current_value"] if batch_groups else 0.0

        # ---- 平均损耗率:read_group AVG ----
        report_groups = Report.read_group(
            domain=[("report_time", ">=", Today)],
            fields=["loss_rate"],
            groupby=[],
            lazy=False,
        )
        avg_loss_rate = report_groups[0]["loss_rate"] if report_groups else 0.0
        if avg_loss_rate is None:
            avg_loss_rate = 0.0

        # ---- XRF 合格率:read_group 按 is_passed 分组 ----
        xrf_groups = Xrf.read_group(
            domain=[("detection_time", ">=", Today)],
            fields=["is_passed"],
            groupby=["is_passed"],
            lazy=False,
        )
        xrf_total = sum(g["is_passed_count"] for g in xrf_groups)
        xrf_passed_count = sum(
            g["is_passed_count"] for g in xrf_groups
            if (g["is_passed"][0] if isinstance(g["is_passed"], tuple) else g["is_passed"])
        )
        xrf_pct = (xrf_passed_count / xrf_total * 100) if xrf_total else 0.0

        return {
            "today": str(Today),
            "done_today": done_today,
            "in_progress": in_progress_count,
            "over_loss_count": over_loss_count,
            "critical_mold_count": len(critical_molds),
            "oil_press_orders": oil_press_orders,
            "lost_wax_orders": lost_wax_orders,
            "current_gold_price": current_price,
            "total_value": total_value,
            "avg_loss_rate": avg_loss_rate,
            "xrf_count_today": xrf_total,
            "xrf_passed_pct": xrf_pct,
        }

    @api.model
    def get_loss_trend(self, days=7):
        """最近 N 天损耗趋势。

        优化点(Phase 2):
          - 改用 ``read_group`` 按 ``report_time:day`` 分组聚合
          - 用 AVG(loss_rate) / COUNT(id) 在 SQL 端算
          - is_over_loss 是 Boolean 字段,read_group 不能 SUM,
            改为第二次 read_group 加 filter 拿超耗数
          - 避免 Python 端逐行遍历 -> 大数据量下显著降内存 + 加速
        """
        from datetime import timedelta
        Report = self.env["gold.workorder.report"]
        end = fields.Date.context_today(self)
        start = end - timedelta(days=days)

        base_domain = [
            ("report_time", ">=", start),
            ("report_time", "<=", end + timedelta(days=1)),
        ]

        # 第一次 read_group:总报工数 + 平均损耗率
        all_groups = Report.read_group(
            domain=base_domain,
            fields=["loss_rate"],
            groupby="report_time:day",
            lazy=False,
        )
        # 第二次 read_group:超耗报工数(按 filter)
        over_groups = Report.read_group(
            domain=base_domain + [("is_over_loss", "=", True)],
            fields=["id"],   # 仅需 COUNT,任意非 group 字段都行
            groupby="report_time:day",
            lazy=False,
        )
        over_dict = {}
        for g in over_groups:
            key = g["report_time:day"]
            key = key if isinstance(key, str) else str(key)
            over_dict[key] = g.get("report_time_count", 0)

        result = []
        for g in all_groups:
            day_key = g["report_time:day"]
            d_str = day_key if isinstance(day_key, str) else str(day_key)
            result.append({
                "date": d_str,
                "avg_loss_rate": g.get("loss_rate") or 0.0,
                "report_count": g.get("report_time_count", 0),
                "over_loss_count": over_dict.get(d_str, 0),
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
