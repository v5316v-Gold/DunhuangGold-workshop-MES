# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 生产后 REST API
=====================================

生产后闭环端点(盘库 / 成品入库 / 班后回料):

  POST /dunhuanggold_workshop_mes/api/v1/inventory/count       创建金料盘点单
  GET  /dunhuanggold_workshop_mes/api/v1/inventory/list        盘点单列表
  POST /dunhuanggold_workshop_mes/api/v1/finished_goods/post   成品入库(按件级 SN)
  POST /dunhuanggold_workshop_mes/api/v1/material_return/confirm 班后回料
"""

import json
import logging

from odoo import http, fields
from odoo.http import request
from odoo.exceptions import UserError, ValidationError

from odoo.addons.dunhuanggold_workshop_mes.tools.rate_limit import rate_limit

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


class GoldPostprodApiController(http.Controller):
    """生产后闭环 API"""

    # ----- 金料盘点: 创建盘点单 -----
    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/inventory/count",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    @rate_limit(calls=30, period=60, key="inventory_count", scope="user")
    def inventory_count(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data or "{}")
        except json.JSONDecodeError:
            return _json_err("Invalid JSON")
        lines = data.get("lines") or []
        if not lines:
            return _json_err("lines required")
        try:
            line_vals = []
            for line in lines:
                batch_id = line.get("batch_id")
                if not batch_id:
                    return _json_err("每行需提供 batch_id")
                line_vals.append((0, 0, {
                    "batch_id": batch_id,
                    "actual_weight_g": line.get("actual_weight_g", 0.0),
                    "note": line.get("note"),
                }))
            rec = request.env["gold.inventory.count"].create({
                "inventory_date": data.get("inventory_date") or fields.Date.context_today(request.env.user),
                "location_id": data.get("location_id"),
                "scope_note": data.get("scope_note"),
                "counter_id": data.get("counter_id") or request.env.user.id,
                "reviewer_id": data.get("reviewer_id"),
                "line_ids": line_vals,
                "note": data.get("note"),
            })
            if data.get("start", False):
                rec.action_start()
            return _json_ok({
                "id": rec.id,
                "name": rec.name,
                "state": rec.state,
                "total_diff_g": rec.total_diff_g,
            })
        except (ValidationError, UserError) as e:
            return _json_err(str(e), 400)
        except Exception as e:
            _logger.exception("盘点单创建异常")
            return _json_err(f"系统错误: {e}", 500)

    # ----- 金料盘点: 列表 -----
    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/inventory/list",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def inventory_list(self, **kwargs):
        counts = request.env["gold.inventory.count"].search(
            [], order="inventory_date desc", limit=100
        )
        return _json_ok([{
            "id": c.id,
            "name": c.name,
            "inventory_date": c.inventory_date,
            "state": c.state,
            "total_book_weight_g": c.total_book_weight_g,
            "total_actual_weight_g": c.total_actual_weight_g,
            "total_diff_g": c.total_diff_g,
        } for c in counts])

    # ----- 成品入库: 按件级 SN -----
    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/finished_goods/post",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    @rate_limit(calls=60, period=60, key="finished_goods_post", scope="user")
    def finished_goods_post(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data or "{}")
        except json.JSONDecodeError:
            return _json_err("Invalid JSON")
        sns = data.get("piece_sns") or []
        if not sns:
            return _json_err("piece_sns required")
        try:
            pieces = request.env["gold.piece"].search([("sn", "in", sns)])
            found = set(pieces.mapped("sn"))
            missing = [sn for sn in sns if sn not in found]
            if missing:
                return _json_err("SN 不存在: %s" % ", ".join(missing))
            non_finished = pieces.filtered(lambda p: p.state != "finished")
            if non_finished:
                return _json_err(
                    "以下 SN 未完工: %s" % ", ".join(non_finished.mapped("sn"))
                )
            line_vals = [(0, 0, {
                "piece_id": p.id,
                "actual_weight_g": p.actual_weight_g or 0.0,
            }) for p in pieces]
            rec = request.env["gold.finished.goods"].create({
                "post_date": data.get("post_date") or fields.Date.context_today(request.env.user),
                "production_id": data.get("production_id"),
                "location_id": data.get("location_id"),
                "generate_batch": data.get("generate_batch", False),
                "line_ids": line_vals,
                "note": data.get("note"),
            })
            rec.action_post()
            return _json_ok({
                "id": rec.id,
                "name": rec.name,
                "state": rec.state,
                "total_piece_count": rec.total_piece_count,
                "total_weight_g": rec.total_weight_g,
                "batch_id": rec.batch_id.id if rec.batch_id else None,
            })
        except (ValidationError, UserError) as e:
            return _json_err(str(e), 400)
        except Exception as e:
            _logger.exception("成品入库异常")
            return _json_err(f"系统错误: {e}", 500)

    # ----- 班后回料 -----
    @http.route(
        "/dunhuanggold_workshop_mes/api/v1/material_return/confirm",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    @rate_limit(calls=60, period=60, key="material_return_confirm", scope="user")
    def material_return_confirm(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data or "{}")
        except json.JSONDecodeError:
            return _json_err("Invalid JSON")
        if not data.get("product_id"):
            return _json_err("product_id required")
        if not data.get("weight_g"):
            return _json_err("weight_g required")
        try:
            rec = request.env["gold.material.return"].create({
                "return_date": data.get("return_date") or fields.Date.context_today(request.env.user),
                "production_id": data.get("production_id"),
                "workorder_id": data.get("workorder_id"),
                "report_id": data.get("report_id"),
                "workstation_id": data.get("workstation_id"),
                "operator_id": data.get("operator_id") or request.env.user.id,
                "return_source": data.get("return_source", "gate"),
                "material_type": data.get("material_type", "gold"),
                "product_id": data["product_id"],
                "weight_g": data["weight_g"],
                "create_new_batch": data.get("create_new_batch", True),
                "target_batch_id": data.get("target_batch_id"),
                "note": data.get("note"),
            })
            rec.action_confirm()
            return _json_ok({
                "id": rec.id,
                "name": rec.name,
                "state": rec.state,
                "batch_id": rec.batch_id.id if rec.batch_id else None,
            })
        except (ValidationError, UserError) as e:
            return _json_err(str(e), 400)
        except Exception as e:
            _logger.exception("班后回料异常")
            return _json_err(f"系统错误: {e}", 500)
