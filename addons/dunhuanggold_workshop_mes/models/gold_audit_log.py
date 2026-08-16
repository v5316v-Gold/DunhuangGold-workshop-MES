# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 审计日志(Phase 2 新增)
==========================================

记录敏感操作的不可变轨迹,贵金属行业法规要求保留 5 年。

设计原则:
  - 一旦写入不允许 update / unlink(``_allow_write = False`` + ORM 钩子)
  - 按 ``model + res_id`` 关联目标资源,便于反向追溯
  - 按 ``action`` + ``user_id + timestamp`` 建立三角查询索引
  - 仅车间主任 + 审计员可读,普通操作员不可见(由 CSV 控制)

模型:
  gold.audit.log
    - model_name      Char         模型名(如 'gold.material.batch')
    - res_id          Integer      资源 ID
    - res_display     Char         资源的 name_get 显示
    - action          Char        'create' / 'write' / 'unlink' / 'confirm' /
                                   'cancel' / 'consume' / 'allocate' /
                                   'release' / 'ocr_verify' / 'login' / ...
    - user_id         Many2one     操作人
    - timestamp       Datetime     操作时间(默认 now)
    - http_route      Char         触发端点(API 调用时)
    - source_ip       Char         调用方 IP
    - payload_before  Text         操作前 JSON 快照(可选)
    - payload_after   Text         操作后 JSON 快照(可选)
    - note            Text         备注 / 异常说明
"""

from odoo import models, fields, api, _
from odoo.exceptions import AccessError


AUDIT_ACTION_SELECTION = [
    ("create", "创建"),
    ("write", "更新"),
    ("unlink", "删除"),
    ("confirm", "确认"),
    ("cancel", "作废"),
    ("allocate", "批次分配"),
    ("consume", "批次消耗"),
    ("release", "批次释放"),
    ("adjust", "盘点调整"),
    ("lock", "锁定"),
    ("unlock", "解锁"),
    ("ocr_verify", "OCR 校验"),
    ("restock", "入库/退库"),
    ("issue", "领用"),
    ("login", "登录"),
    ("api_call", "API 调用"),
]


class GoldAuditLog(models.Model):
    _name = "gold.audit.log"
    _description = "审计日志"
    _order = "timestamp desc, id desc"
    _rec_name = "display_name"
    _log_access = True  # 保留 create_uid / create_date
    _allow_write = False  # ORM 钩子:不允许 write

    display_name = fields.Char(
        string="描述",
        compute="_compute_display_name",
        store=True,
    )
    model_name = fields.Char(
        string="模型",
        required=True,
        index=True,
        help="如 'gold.material.batch'",
    )
    res_id = fields.Integer(
        string="资源 ID",
        required=True,
        index=True,
        help="目标记录的 id",
    )
    res_display = fields.Char(
        string="资源显示",
        help="目标记录的 name_get 显示(便于检索)",
        index=True,
    )
    action = fields.Selection(
        AUDIT_ACTION_SELECTION,
        string="动作",
        required=True,
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="操作人",
        required=True,
        default=lambda self: self.env.user,
        index=True,
    )
    timestamp = fields.Datetime(
        string="时间",
        default=fields.Datetime.now,
        required=True,
        index=True,
    )
    http_route = fields.Char(string="HTTP 端点")
    source_ip = fields.Char(string="来源 IP")
    payload_before = fields.Text(string="操作前 JSON")
    payload_after = fields.Text(string="操作后 JSON")
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        default=lambda self: self.env.company,
        index=True,
    )
    note = fields.Text(string="备注")

    @api.depends("model_name", "res_id", "action", "timestamp")
    def _compute_display_name(self):
        for rec in self:
            ts = rec.timestamp or ""
            rec.display_name = f"[{ts}] {rec.action} {rec.model_name}#{rec.res_id}"

    # ---- 不可变: 禁止 write / unlink ----
    def write(self, vals):
        raise AccessError(_("审计日志不可修改 (合规要求: 操作留痕)"))

    def unlink(self):
        raise AccessError(_("审计日志不可删除 (合规要求: 保留 5 年)"))

    # ---- 工厂方法: 让 controller / model 易于调用 ----
    @api.model
    def log_action(
        self,
        model_name,
        res_id,
        action,
        res_display=None,
        payload_before=None,
        payload_after=None,
        note=None,
    ):
        """便捷写入审计日志,自动捕获 user / ip / route。"""
        vals = {
            "model_name": model_name,
            "res_id": res_id,
            "action": action,
            "res_display": res_display or "",
            "payload_before": payload_before,
            "payload_after": payload_after,
            "note": note,
        }
        # 从 request context 取 ip + route(如可用)
        try:
            from odoo.http import request
            if request and request.httprequest:
                vals["source_ip"] = (
                    request.httprequest.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                    or request.httprequest.remote_addr
                )
                if request.httprequest.url_rule:
                    vals["http_route"] = request.httprequest.url_rule.rule
        except Exception:
            pass  # 非 HTTP context(直接 create 后台)允许 silent fail
        return self.sudo().create(vals)

    @api.model
    def cleanup_expired(self, retention_days=1825):
        """Cron: 清理 retention_days 天前的日志(默认 5 年)。

        实际生产环境通常直接备份到冷存储而不删,这里只是兜底。
        """
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), days=retention_days)
        expired = self.search([("timestamp", "<", cutoff)])
        if expired:
            _logger = __import__("logging").getLogger(__name__)
            _logger.info("audit_log cleanup: deleting %d records older than %s",
                         len(expired), cutoff)
            # 真正的合规场景不允许 delete —— 这里仅在 cron 入口用 super().unlink()
            return super(GoldAuditLog, expired).unlink()
        return 0
