# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 控制器入口
=============================
"""

from odoo import http
from odoo.http import request


class GoldMESMainController(http.Controller):
    """车间 ERP 主页 / 看板"""

    @http.route("/dunhuang_gold_mes", type="http", auth="user", website=True)
    def index(self, **kwargs):
        """车间首页"""
        return request.render("dunhuang_gold_mes.dashboard_template", {})

    @http.route("/dunhuang_gold_mes/dashboard", type="http", auth="user", website=True)
    def dashboard(self, **kwargs):
        """看板页面"""
        return request.render("dunhuang_gold_mes.dashboard_template", {})
