# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 人机料法环补全 REST API
=============================================

新增端点(人机料法环之「环 / 机 / 人」):

  环 (Environment):
    POST /dunhuanggold_workshop_mes/api/v1/environment/reading   环境读数上报
    GET  /dunhuanggold_workshop_mes/api/v1/environment/latest    最新环境读数
    GET  /dunhuanggold_workshop_mes/api/v1/environment/alarms    环境超限报警
    POST /dunhuanggold_workshop_mes/api/v1/hazchem/issue         危化品领用(双人双锁)
    GET  /dunhuanggold_workshop_mes/api/v1/hazchem/list          危化品台账列表
    POST /dunhuanggold_workshop_mes/api/v1/energy/reading        能耗读数上报

  机 (Machine):
    POST /dunhuanggold_workshop_mes/api/v1/maintenance/order     设备维护工单上报
    GET  /dunhuanggold_workshop_mes/api/v1/maintenance/list      维护工单列表

  人 (Man):
    GET  /dunhuanggold_workshop_mes/api/v1/certificate/verify    人员资质校验
"""

import json
import logging

from odoo import http, fields
from odoo.http import request
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


def _json_ok(data=None, msg="ok"):
    return request.make_response(
        json.dumps({"ok": True, "msg": msg, "data": data or {}}, default=str, ensure_ascii=False),
        headers=[("Content-Type", "application/json")],
    )


def _json_err(msg, status=400):
    return request.make_response(
        json.dumps({"ok": False, "error": msg}, ensure_ascii=False),
        headers=[("Content-Type", "application/json")],
        status=status,
    )


class GoldEhsApiController(http.Controller):
    """环境安全 / 维护 / 资质 API"""

    # ----- 环: 环境读数上报 -----
    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/environment/reading",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def environment_reading(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data or "{}")
        except json.JSONDecodeError:
            return _json_err("Invalid JSON")
        sensor_code = data.get("sensor_code")
        if not sensor_code:
            return _json_err("sensor_code required")
        sensor = request.env["gold.environment.sensor"].search(
            [("code", "=", sensor_code)], limit=1
        )
        if not sensor:
            return _json_err("传感器不存在", 404)
        if "value" not in data:
            return _json_err("value required")
        try:
            rec = request.env["gold.environment.reading"].create({
                "sensor_id": sensor.id,
                "value": data["value"],
                "reading_time": data.get("reading_time") or fields.Datetime.now(),
                "source": data.get("source", "rest_api"),
                "note": data.get("note"),
            })
            return _json_ok({
                "id": rec.id,
                "state": rec.state,
                "alarm_desc": rec.alarm_desc,
            })
        except (ValidationError, UserError) as e:
            return _json_err(str(e), 400)
        except Exception as e:
            _logger.exception("环境读数上报异常")
            return _json_err(f"系统错误: {e}", 500)

    # ----- 环: 最新环境读数 -----
    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/environment/latest",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def environment_latest(self, **kwargs):
        sensors = request.env["gold.environment.sensor"].search([("active", "=", True)])
        if not sensors:
            return _json_ok([])
        readings = request.env["gold.environment.reading"].search(
            [("sensor_id", "in", sensors.ids)],
            order="reading_time desc",
            limit=len(sensors) * 2,
        )
        # 每个传感器取最新一条
        latest = {}
        for r in readings:
            if r.sensor_id.id not in latest:
                latest[r.sensor_id.id] = r
        return _json_ok([{
            "sensor_code": r.sensor_id.code,
            "sensor_name": r.sensor_id.name,
            "sensor_type": r.sensor_id.sensor_type,
            "value": r.value,
            "unit": r.unit,
            "state": r.state,
            "alarm_desc": r.alarm_desc,
            "reading_time": r.reading_time,
        } for r in latest.values()])

    # ----- 环: 环境超限报警 -----
    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/environment/alarms",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def environment_alarms(self, **kwargs):
        readings = request.env["gold.environment.reading"].search(
            [("state", "=", "alarm")],
            order="reading_time desc",
            limit=100,
        )
        return _json_ok([{
            "id": r.id,
            "sensor_code": r.sensor_id.code,
            "sensor_name": r.sensor_id.name,
            "value": r.value,
            "unit": r.unit,
            "alarm_desc": r.alarm_desc,
            "reading_time": r.reading_time,
        } for r in readings])

    # ----- 环: 危化品台账列表 -----
    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/hazchem/list",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def hazchem_list(self, **kwargs):
        chems = request.env["gold.hazardous.chemical"].search([("active", "=", True)])
        return _json_ok([{
            "id": c.id,
            "code": c.code,
            "name": c.name,
            "category": c.category,
            "danger_level": c.danger_level,
            "lock_required": c.lock_required,
            "stock_qty": c.stock_qty,
            "stock_unit": c.stock_unit,
            "safety_stock": c.safety_stock,
        } for c in chems])

    # ----- 环: 危化品领用 -----
    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/hazchem/issue",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def hazchem_issue(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data or "{}")
        except json.JSONDecodeError:
            return _json_err("Invalid JSON")
        chem_code = data.get("chemical_code")
        qty = data.get("qty")
        if not chem_code or qty is None:
            return _json_err("chemical_code/qty required")
        chem = request.env["gold.hazardous.chemical"].search(
            [("code", "=", chem_code)], limit=1
        )
        if not chem:
            return _json_err("危化品不存在", 404)
        try:
            usage = request.env["gold.hazardous.chemical.usage"].create({
                "chemical_id": chem.id,
                "usage_type": data.get("usage_type", "issue"),
                "qty": qty,
                "requester_id": data.get("requester_id") or request.env.user.id,
                "keeper_id": data.get("keeper_id") or chem.keeper_id.id,
                "approver_id": data.get("approver_id"),
                "dual_custody_confirmed": data.get("dual_custody_confirmed", False),
                "purpose": data.get("purpose"),
                "production_id": data.get("production_id"),
                "workstation_id": data.get("workstation_id"),
                "usage_time": data.get("usage_time") or fields.Datetime.now(),
            })
            if data.get("confirm", False):
                usage.action_confirm()
            return _json_ok({
                "id": usage.id,
                "name": usage.name,
                "state": usage.state,
            })
        except (ValidationError, UserError) as e:
            return _json_err(str(e), 400)
        except Exception as e:
            _logger.exception("危化品领用异常")
            return _json_err(f"系统错误: {e}", 500)

    # ----- 环: 能耗读数上报 -----
    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/energy/reading",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def energy_reading(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data or "{}")
        except json.JSONDecodeError:
            return _json_err("Invalid JSON")
        meter_code = data.get("meter_code")
        if not meter_code:
            return _json_err("meter_code required")
        meter = request.env["gold.energy.meter"].search(
            [("code", "=", meter_code)], limit=1
        )
        if not meter:
            return _json_err("表计不存在", 404)
        if "cumulative_value" not in data:
            return _json_err("cumulative_value required")
        try:
            rec = request.env["gold.energy.reading"].create({
                "meter_id": meter.id,
                "cumulative_value": data["cumulative_value"],
                "reading_time": data.get("reading_time") or fields.Datetime.now(),
                "source": data.get("source", "rest_api"),
                "note": data.get("note"),
            })
            return _json_ok({
                "id": rec.id,
                "period_consumption": rec.period_consumption,
                "period_amount": rec.period_amount,
            })
        except (ValidationError, UserError) as e:
            return _json_err(str(e), 400)
        except Exception as e:
            _logger.exception("能耗读数上报异常")
            return _json_err(f"系统错误: {e}", 500)

    # ----- 机: 维护工单上报 -----
    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/maintenance/order",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def maintenance_order(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data or "{}")
        except json.JSONDecodeError:
            return _json_err("Invalid JSON")
        equipment_code = data.get("equipment_code")
        if not equipment_code:
            return _json_err("equipment_code required")
        equip = request.env["gold.equipment"].search(
            [("code", "=", equipment_code)], limit=1
        )
        if not equip:
            return _json_err("设备不存在", 404)
        try:
            rec = request.env["gold.maintenance.order"].create({
                "equipment_id": equip.id,
                "maintenance_type": data.get("maintenance_type", "cm"),
                "priority": data.get("priority", "1"),
                "assignee_id": data.get("assignee_id"),
                "planned_date": data.get("planned_date"),
                "description": data.get("description"),
                "down_before": data.get("down_before", False),
            })
            if data.get("start", False):
                rec.action_start()
            return _json_ok({"id": rec.id, "name": rec.name, "state": rec.state})
        except (ValidationError, UserError) as e:
            return _json_err(str(e), 400)
        except Exception as e:
            _logger.exception("维护工单上报异常")
            return _json_err(f"系统错误: {e}", 500)

    # ----- 机: 维护工单列表 -----
    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/maintenance/list",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def maintenance_list(self, **kwargs):
        orders = request.env["gold.maintenance.order"].search(
            [], order="priority desc, planned_date asc", limit=100
        )
        return _json_ok([{
            "id": o.id,
            "name": o.name,
            "equipment": o.equipment_id.name,
            "maintenance_type": o.maintenance_type,
            "priority": o.priority,
            "state": o.state,
            "assignee": o.assignee_id.name if o.assignee_id else "",
            "planned_date": o.planned_date,
        } for o in orders])

    # ----- 人: 资质校验 -----
    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/certificate/verify",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def certificate_verify(self, **kwargs):
        user_id = kwargs.get("user_id")
        cert_type = kwargs.get("cert_type")
        if not user_id:
            return _json_err("user_id required")
        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            return _json_err("user_id 必须为整数")
        domain = [("holder_id", "=", user_id_int), ("is_valid", "=", True)]
        if cert_type:
            domain.append(("cert_type", "=", cert_type))
        certs = request.env["gold.employee.certificate"].search(domain)
        return _json_ok({
            "user_id": user_id_int,
            "cert_type": cert_type,
            "qualified": bool(certs),
            "certificates": [{
                "id": c.id,
                "name": c.name,
                "cert_type": c.cert_type,
                "cert_level": c.cert_level,
                "expiry_date": c.expiry_date,
                "days_to_expire": c.days_to_expire,
            } for c in certs],
        })
