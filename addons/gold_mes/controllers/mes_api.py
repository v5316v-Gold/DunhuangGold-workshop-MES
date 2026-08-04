# -*- coding: utf-8 -*-
"""
贵金属车间 ERP — MES REST API
==============================

端点列表(供工位 PDA / 移动端 / 看板调用):

  POST /gold_mes/api/v1/login
       工位登录

  GET  /gold_mes/api/v1/production/<id>
       获取生产订单详情

  GET  /gold_mes/api/v1/workorder/by_station/<station_id>
       工位获取当前待执行工单

  POST /gold_mes/api/v1/workorder_report
       工序报工(电子天平直采)

  GET  /gold_mes/api/v1/batch/<batch_no>
       查询金料批次

  POST /gold_mes/api/v1/batch/allocate
       分配批次重量

  GET  /gold_mes/api/v1/price/current
       当前金价

  POST /gold_mes/api/v1/price/push
       推送金价(SGE / LBMA)

  POST /gold_mes/api/v1/imprint/verify
       印记 OCR 校验

  POST /gold_mes/api/v1/xrf/save
       XRF 检测结果保存

  GET  /gold_mes/api/v1/dashboard/kpi
       看板 KPI 数据
"""

import json
import logging
from datetime import datetime, timedelta

from odoo import http, _, fields
from odoo.http import request
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class GoldMESApiController(http.Controller):
    """MES REST API"""

    # ----- 通用辅助 -----
    def _json_response(self, data, status=200):
        return request.make_response(
            json.dumps(data, default=str, ensure_ascii=False),
            headers=[("Content-Type", "application/json")],
            status=status,
        )

    def _error(self, msg, status=400):
        return self._json_response({"ok": False, "error": msg}, status)

    def _ok(self, data=None, msg="ok"):
        return self._json_response({"ok": True, "msg": msg, "data": data or {}})

    # ----- 1. 登录 -----
    @http.route(
        "/gold_mes/api/v1/login",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def api_login(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data or "{}")
        except json.JSONDecodeError:
            return self._error("Invalid JSON")
        login = data.get("login")
        password = data.get("password")
        if not login or not password:
            return self._error("login/password required")
        uid = request.session.authenticate(request.db, login, password)
        if not uid:
            return self._error("认证失败", 401)
        user = request.env["res.users"].browse(uid)
        return self._ok({
            "uid": uid,
            "name": user.name,
            "groups": [g.full_name for g in user.groups_id],
        })

    # ----- 2. 生产订单 -----
    @http.route(
        "/gold_mes/api/v1/production/<int:prod_id>",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def api_production_get(self, prod_id, **kwargs):
        rec = request.env["mrp.production"].browse(prod_id)
        if not rec.exists():
            return self._error("生产订单不存在", 404)
        return self._ok({
            "id": rec.id,
            "name": rec.name,
            "product": rec.product_id.display_name,
            "process_type": rec.gold_process_type,
            "route": rec.gold_route_id.name if rec.gold_route_id else None,
            "qty": rec.product_qty,
            "state": rec.gold_state,
            "planned_weight_g": rec.gold_planned_weight_g,
            "actual_weight_g": rec.gold_actual_weight_g,
            "actual_loss_g": rec.gold_actual_loss_g,
            "actual_loss_rate": rec.gold_actual_loss_rate,
            "planned_loss_rate": rec.gold_planned_loss_rate,
            "loss_diff_pct": rec.gold_loss_diff_pct,
        })

    # ----- 3. 工位待执行工单 -----
    @http.route(
        "/gold_mes/api/v1/workorder/by_station/<int:station_id>",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def api_workorder_by_station(self, station_id, **kwargs):
        Workorder = request.env["mrp.workorder"]
        workorders = Workorder.search([
            ("gold_workstation_id", "=", station_id),
            ("state", "in", ["pending", "ready", "progress"]),
        ])
        return self._ok([{
            "id": wo.id,
            "production": wo.production_id.name,
            "operation": wo.operation_id.name if wo.operation_id else None,
            "state": wo.state,
            "standard_time_hours": wo.gold_standard_time_hours,
            "standard_loss_rate": wo.gold_standard_loss_rate,
        } for wo in workorders])

    # ----- 4. 工序报工 -----
    @http.route(
        "/gold_mes/api/v1/workorder_report",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def api_workorder_report(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data or "{}")
        except json.JSONDecodeError:
            return self._error("Invalid JSON")
        required = ["production_id", "operation_id", "input_weight_g", "output_weight_g"]
        for k in required:
            if k not in data:
                return self._error(f"字段缺失: {k}")
        try:
            rec = request.env["gold.workorder.report"].create({
                "production_id": data["production_id"],
                "operation_id": data["operation_id"],
                "workorder_id": data.get("workorder_id"),
                "workstation_id": data.get("workstation_id"),
                "equipment_id": data.get("equipment_id"),
                "operator_id": data.get("operator_id") or request.env.user.id,
                "input_batch_id": data.get("input_batch_id"),
                "input_weight_g": data["input_weight_g"],
                "output_weight_g": data["output_weight_g"],
                "output_piece_count": data.get("output_piece_count", 1),
                "work_hours": data.get("work_hours", 0.0),
                "start_time": data.get("start_time"),
                "end_time": data.get("end_time"),
                "source": data.get("source", "rest_api"),
                "balance_id": data.get("balance_id"),
                "quality_state": data.get("quality_state", "passed"),
                "note": data.get("note"),
            })
            # 触发损耗追溯
            trace = request.env["gold.loss.trace"].create_from_report(rec.id)
            return self._ok({
                "id": rec.id,
                "name": rec.name,
                "loss_g": rec.loss_g,
                "loss_rate": rec.loss_rate,
                "loss_diff_pct": rec.loss_diff_pct,
                "is_over_loss": rec.is_over_loss,
                "trace_id": trace.id if trace else None,
            })
        except (ValidationError, UserError) as e:
            return self._error(str(e), 400)
        except Exception as e:
            _logger.exception("工序报工异常")
            return self._error(f"系统错误: {e}", 500)

    # ----- 5. 金料批次查询 -----
    @http.route(
        "/gold_mes/api/v1/batch/<string:batch_no>",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def api_batch_get(self, batch_no, **kwargs):
        batch = request.env["gold.material.batch"].search([("batch_no", "=", batch_no)], limit=1)
        if not batch:
            return self._error("批次不存在", 404)
        return self._ok({
            "id": batch.id,
            "batch_no": batch.batch_no,
            "product": batch.product_id.display_name,
            "purity": batch.gold_purity,
            "net_weight_g": batch.net_weight_g,
            "available_weight_g": batch.available_weight_g,
            "current_price": batch.current_price,
            "current_value": batch.current_value,
            "state": batch.state,
        })

    # ----- 6. 批次分配 -----
    @http.route(
        "/gold_mes/api/v1/batch/allocate",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def api_batch_allocate(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data or "{}")
        except json.JSONDecodeError:
            return self._error("Invalid JSON")
        batch_id = data.get("batch_id")
        weight_g = data.get("weight_g")
        if not batch_id or weight_g is None:
            return self._error("batch_id/weight_g required")
        batch = request.env["gold.material.batch"].browse(batch_id)
        if not batch.exists():
            return self._error("批次不存在", 404)
        try:
            batch.allocate(weight_g)
            return self._ok({
                "id": batch.id,
                "allocated_weight_g": batch.allocated_weight_g,
                "available_weight_g": batch.available_weight_g,
            })
        except (ValidationError, UserError) as e:
            return self._error(str(e), 400)

    # ----- 7. 当前金价 -----
    @http.route(
        "/gold_mes/api/v1/price/current",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def api_price_current(self, **kwargs):
        gold_type = kwargs.get("gold_type", "au9999")
        source = kwargs.get("source", "sge")
        price = request.env["gold.price.engine"].get_current_price(gold_type, source)
        return self._ok({
            "gold_type": gold_type,
            "source": source,
            "price": price,
            "timestamp": fields.Datetime.now(),
        })

    # ----- 8. 金价推送 -----
    @http.route(
        "/gold_mes/api/v1/price/push",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def api_price_push(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data or "{}")
        except json.JSONDecodeError:
            return self._error("Invalid JSON")
        try:
            rec = request.env["gold.price.engine"].create({
                "price_time": data.get("price_time") or fields.Datetime.now(),
                "source": data.get("source", "sge"),
                "gold_type": data.get("gold_type", "au9999"),
                "price_open": data.get("price_open", 0.0),
                "price_high": data.get("price_high", 0.0),
                "price_low": data.get("price_low", 0.0),
                "price_close": data["price_close"],
                "volume_kg": data.get("volume_kg", 0.0),
                "open_interest": data.get("open_interest", 0.0),
                "is_settlement": data.get("is_settlement", False),
            })
            # 刷新批次当前价
            request.env["gold.price.engine"].update_batch_prices()
            return self._ok({"id": rec.id, "name": rec.price_time})
        except Exception as e:
            return self._error(str(e), 400)

    # ----- 9. 印记 OCR 校验 -----
    @http.route(
        "/gold_mes/api/v1/imprint/verify",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def api_imprint_verify(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data or "{}")
        except json.JSONDecodeError:
            return self._error("Invalid JSON")
        imprint_id = data.get("imprint_id")
        expected = data.get("expected")
        if not imprint_id:
            return self._error("imprint_id required")
        rec = request.env["gold.imprint"].browse(imprint_id)
        if not rec.exists():
            return self._error("印记记录不存在", 404)
        try:
            ok = rec.action_ocr_verify(expected)
            return self._ok({
                "id": rec.id,
                "verified": rec.ocr_verified,
                "mismatch": rec.ocr_mismatch,
                "content": rec.imprint_content,
                "passed": ok,
            })
        except Exception as e:
            return self._error(str(e), 400)

    # ----- 10. XRF 检测保存 -----
    @http.route(
        "/gold_mes/api/v1/xrf/save",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def api_xrf_save(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data or "{}")
        except json.JSONDecodeError:
            return self._error("Invalid JSON")
        try:
            rec = request.env["gold.xrf.record"].create({
                "production_id": data.get("production_id"),
                "product_id": data.get("product_id"),
                "batch_id": data.get("batch_id"),
                "equipment_id": data.get("equipment_id"),
                "operator_id": data.get("operator_id") or request.env.user.id,
                "approver_id": data.get("approver_id"),
                "method": data.get("method", "standard"),
                "gold_pct": data.get("gold_pct", 0.0),
                "platinum_pct": data.get("platinum_pct", 0.0),
                "palladium_pct": data.get("palladium_pct", 0.0),
                "silver_pct": data.get("silver_pct", 0.0),
                "copper_pct": data.get("copper_pct", 0.0),
                "zinc_pct": data.get("zinc_pct", 0.0),
                "nickel_pct": data.get("nickel_pct", 0.0),
                "standard_pct": data.get("standard_pct", 99.00),
                "duration_seconds": data.get("duration_seconds", 0.0),
            })
            return self._ok({
                "id": rec.id,
                "is_passed": rec.is_passed,
                "main_metal_pct": rec.main_metal_pct,
            })
        except Exception as e:
            return self._error(str(e), 400)

    # ----- 11. 看板 KPI -----
    @http.route(
        "/gold_mes/api/v1/dashboard/kpi",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def api_dashboard_kpi(self, **kwargs):
        Process = request.env["mrp.production"]
        today = fields.Date.context_today(request.env["res.users"].browse(request.uid))

        # 当日完工
        done_today = Process.search([
            ("gold_state", "=", "done"),
            ("date_finished", ">=", today),
        ])
        # 进行中
        in_progress = Process.search([("gold_state", "=", "in_progress")])
        # 异常工序
        over_loss = request.env["gold.workorder.report"].search([
            ("is_over_loss", "=", True),
            ("report_time", ">=", today),
        ])
        # 模具寿命预警
        Mold = request.env["gold.mold"]
        critical = Mold.search([("state", "!=", "scrapped")]).filtered(
            lambda m: m.remaining_count <= m.rated_life_count * m.life_warning_pct / 100
        )

        # 油压线 / 失蜡线分布
        oil_press = Process.search([("gold_process_type", "=", "oil_press"), ("gold_state", "in", ["confirmed", "in_progress"])])
        lost_wax = Process.search([("gold_process_type", "=", "lost_wax"), ("gold_state", "in", ["confirmed", "in_progress"])])

        # 当前金价
        current_price = request.env["gold.price.engine"].get_current_price("au9999")

        return self._ok({
            "today": str(today),
            "done_today": len(done_today),
            "in_progress": len(in_progress),
            "over_loss_today": len(over_loss),
            "critical_mold_count": len(critical),
            "oil_press_orders": len(oil_press),
            "lost_wax_orders": len(lost_wax),
            "current_gold_price": current_price,
        })
