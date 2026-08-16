"""
敦煌金加工车间 ERP — 设备接入适配(预留)
====================================

预留接口:
  - MQTT 接入: dunhuanggold_workshop_mes/api/v1/device/mqtt/payload
  - OPC UA 桥接: 通过外部服务把 OPC UA 节点值 POST
  - Modbus 接入: 通过 Edge Gateway 转 JSON
  - 电子天平 RS-232: 通过串口服务器转 JSON

设计上采用 JSON 统一负载,字段:
  {
    "device_code": "OBP-001",
    "timestamp": "2026-08-05T10:30:00Z",
    "protocol": "opc_ua | modbus | mqtt | rs232",
    "metrics": {
      "weight_g": 5.123,
      "temperature_c": 850.0,
      "vacuum_kpa": 5.2,
      "current_a": 12.3,
      "...": "..."
    }
  }

设备协议适配层为独立服务(不在 Odoo 内),这里只接收 JSON 并落库到设备历史。
"""
# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime

from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class GoldDeviceApiController(http.Controller):
    """设备接入 API(适配器层)"""

    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/device/heartbeat",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def device_heartbeat(self, **kwargs):
        """
        设备心跳上报
        Body: {device_code, state, runtime_hours, oee_total_count, oee_good_count}
        """
        try:
            data = json.loads(request.httprequest.data or "{}")
        except json.JSONDecodeError:
            return _json_err("Invalid JSON")
        code = data.get("device_code")
        if not code:
            return _json_err("device_code required")
        equip = request.env["gold.equipment"].search([("code", "=", code)], limit=1)
        if not equip:
            return _json_err("设备不存在", 404)
        # 更新状态
        vals = {}
        if "state" in data:
            vals["state"] = data["state"]
        if "runtime_hours" in data:
            vals["oee_runtime_hours"] = data["runtime_hours"]
        if "downtime_hours" in data:
            vals["oee_downtime_hours"] = data["downtime_hours"]
        if "total_count" in data:
            vals["oee_total_count"] = data["total_count"]
        if "good_count" in data:
            vals["oee_good_count"] = data["good_count"]
        if vals:
            equip.write(vals)
        return _json_ok({
            "device_code": code,
            "new_state": equip.state,
            "oee": equip.oee,
        })

    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/device/metric",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def device_metric(self, **kwargs):
        """
        设备度量上报(用于实时采集)
        Body: {device_code, metrics: {weight_g: 5.123}, context: {workorder_id?, production_id?}}
        """
        try:
            data = json.loads(request.httprequest.data or "{}")
        except json.JSONDecodeError:
            return _json_err("Invalid JSON")
        code = data.get("device_code")
        metrics = data.get("metrics", {})
        context = data.get("context", {})
        if not code or not metrics:
            return _json_err("device_code/metrics required")
        equip = request.env["gold.equipment"].search([("code", "=", code)], limit=1)
        if not equip:
            return _json_err("设备不存在", 404)
        # 如果是电子天平,联动工序报工
        if equip.category == "balance" and "weight_g" in metrics:
            _logger.info("天平 %s: %.6fg", code, metrics["weight_g"])
            # 工位需要结合 context 决定写入哪个报工
            if context.get("workorder_id"):
                # 更新最新报工的输入/输出重量
                report = request.env["gold.workorder.report"].search([
                    ("workorder_id", "=", context["workorder_id"]),
                    ("state", "=", "confirmed"),
                ], order="report_time desc", limit=1)
                if report and "input_weight_g" in metrics:
                    report.write({"input_weight_g": metrics["weight_g"]})
                elif report and "output_weight_g" in metrics:
                    report.write({"output_weight_g": metrics["weight_g"]})
        # 设备状态更新
        if equip.state == "idle":
            equip.write({"state": "running"})
        return _json_ok({"device_code": code, "metrics_received": list(metrics.keys())})

    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/device/list",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def device_list(self, **kwargs):
        equips = request.env["gold.equipment"].search([])
        return _json_ok([{
            "id": e.id,
            "code": e.code,
            "name": e.name,
            "category": e.category,
            "state": e.state,
            "oee": e.oee,
            "protocol": e.protocol,
            "ip": e.ip_address,
        } for e in equips])


def _json_ok(data=None, msg="ok"):
    return request.make_response(
        json.dumps({"ok": True, "msg": msg, "data": data or {}}, default=str, ensure_ascii=False),
        headers=[("Content-Type", "application/json")],
    )


def _json_err(msg, status=400):
    return request.make_response(
        json.dumps({"ok": False, "error": msg}),
        headers=[("Content-Type", "application/json")],
        status=status,
    )
