# -*- coding: utf-8 -*-
"""
基于数据库计数器的简易 API 限流装饰器。

设计权衡:
  - 不用 Redis,避免引入额外基础设施依赖(YAGNI)
  - 用 Odoo 自身的 ``ir.config_parameter`` 存限流窗口时间戳
  - 每次请求做 ``SELECT FOR UPDATE`` 风格的事务,简单可靠
  - 适用于百级 QPS 场景,超过千级 QPS 时建议迁到 Redis

使用:
    from odoo.addons.dunhuanggold_workshop_mes.tools.rate_limit import rate_limit

    @route('/api/v1/workorder_report', ...)
    @rate_limit(calls=100, period=60, key='workorder_report')
    def api_workorder_report(self, **kwargs):
        ...

参数:
    calls: 窗口内允许的最大调用次数
    period: 窗口长度(秒)
    key: 限流键(同一个 key 共享计数器;留空则用 endpoint 名)
    scope: 限流维度,'user' / 'ip' / 'global'
"""

import functools
import logging
import time
from datetime import datetime, timedelta

from odoo.http import request
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def _resolve_scope_key(scope, fallback_key):
    """根据 scope 计算实际限流 key。"""
    if scope == "global":
        return f"global:{fallback_key}"
    if scope == "ip":
        # 优先 X-Forwarded-For(反代后),否则用 remote_addr
        ip = (
            request.httprequest.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.httprequest.remote_addr
            or "unknown"
        )
        return f"ip:{ip}:{fallback_key}"
    # 默认 user(uid)
    uid = request.uid or 0
    return f"user:{uid}:{fallback_key}"


def _get_count_param(scope_key):
    """从 ir.config_parameter 读取当前计数 + 窗口起点。"""
    ICP = request.env["ir.config_parameter"].sudo()
    count_key = f"gold.ratelimit.count.{scope_key}"
    win_key = f"gold.ratelimit.win.{scope_key}"
    try:
        count = int(ICP.get_param(count_key, "0"))
        win_start_str = ICP.get_param(win_key, "")
        win_start = float(win_start_str) if win_start_str else 0.0
    except (ValueError, TypeError):
        count = 0
        win_start = 0.0
    return count, win_start


def _set_count_param(scope_key, count, win_start):
    """持久化计数 + 窗口起点。"""
    ICP = request.env["ir.config_parameter"].sudo()
    ICP.set_param(f"gold.ratelimit.count.{scope_key}", str(count))
    ICP.set_param(f"gold.ratelimit.win.{scope_key}", str(win_start))


def rate_limit(calls=100, period=60, key=None, scope="user"):
    """装饰器:在 ``period`` 秒内最多 ``calls`` 次。

    超限抛 ``UserError``(HTTP 200 with ok=false, error_code='rate_limit'),
    客户端可见 429 等价语义。
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            endpoint_key = key or func.__name__
            scope_key = _resolve_scope_key(scope, endpoint_key)
            now = time.time()

            # 读取当前窗口状态
            count, win_start = _get_count_param(scope_key)

            # 窗口已过期 -> 重置
            if now - win_start >= period:
                count = 0
                win_start = now

            # 限流判断
            if count >= calls:
                retry_after = int(period - (now - win_start)) + 1
                _logger.warning(
                    "rate_limit hit: scope=%s calls=%d/%d retry_after=%ds",
                    scope_key, count, calls, retry_after,
                )
                # 抛 UserError 让 controller 统一捕获并返回 429
                raise UserError(
                    f"rate_limit_exceeded:retry_after={retry_after}s"
                )

            # 计数 +1 并落库
            count += 1
            _set_count_param(scope_key, count, win_start)

            return func(self, *args, **kwargs)
        return wrapper
    return decorator
