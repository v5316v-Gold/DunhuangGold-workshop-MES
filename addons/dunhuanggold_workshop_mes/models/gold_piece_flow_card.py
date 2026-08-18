# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 工序间交接卡 (Phase 3.1)
========================================

件级 SN 在工序间的扫码交接记录,是数字孪生的基础:
  - 上一道工序完成后,操作员在 PDA 扫 SN → 提交到下一工位
  - 记录: 发送方 / 接收方 / 时间 / 当前重量 / 工序
  - 用于:
    1. WIP 实时追踪(某件现在在哪道工序)
    2. 责任划分(工序间问题归属)
    3. 工序停留时长(瓶颈分析)
    4. 完整追溯链(SN → flow_card 序列 → 全流程重放)

设计:
  - 一件 SN 可有多条 flow_card(每道工序 1 条)
  - 工序开始 = 上条 flow_card.out_operation_id 与当前 in_operation_id 衔接
  - 工序完成 = 触发下一条 flow_card
  - 重工/返工: out_operation_id = in_operation_id(同一工序反复)

状态机:
  in_transit(交接中) → at_station(工位上) → completed(已完成)
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


FLOW_CARD_STATE = [
    ("in_transit", "交接中"),  # 刚扫码,等接收方确认
    ("at_station", "工位上"),  # 接收方已确认
    ("completed", "已离开"),  # 下一道工序已开始
    ("cancelled", "已取消"),
]


class GoldPieceFlowCard(models.Model):
    _name = "gold.piece.flow.card"
    _description = "件级 SN 工序交接卡"
    _order = "handover_time desc, id desc"
    _rec_name = "display_name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    display_name = fields.Char(string="描述", compute="_compute_display_name", store=True)

    # 关联
    piece_id = fields.Many2one(
        "gold.piece",
        string="件级 SN",
        required=True,
        index=True,
        ondelete="cascade",
    )
    production_id = fields.Many2one(
        "mrp.production",
        string="生产订单",
        related="piece_id.production_id",
        store=True,
        index=True,
    )

    # 工序
    in_operation_id = fields.Many2one(
        "gold.process.operation",
        string="接收工序",
        required=True,
        help="本卡接收的工序(即下一道要做的工序)",
        index=True,
    )
    out_operation_id = fields.Many2one(
        "gold.process.operation",
        string="发出工序",
        help="本卡的发出工序(即上一道已完成的工序),空表示首道工序接收",
        index=True,
    )
    in_workstation_id = fields.Many2one(
        "gold.workstation",
        string="接收工位",
        required=True,
        help="件到达的工位",
    )
    out_workstation_id = fields.Many2one(
        "gold.workstation",
        string="发出工位",
        help="件离开的工位",
    )

    # 人员
    sender_id = fields.Many2one(
        "res.users",
        string="发送人",
        required=True,
        default=lambda self: self.env.user,
        help="扫码发出者(上一道工序操作员)",
    )
    receiver_id = fields.Many2one(
        "res.users",
        string="接收人",
        help="扫码接收者(本道工序操作员)",
    )

    # 时间
    handover_time = fields.Datetime(
        string="交接时间",
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    received_time = fields.Datetime(
        string="接收确认时间",
        help="接收方扫码确认到达的时间",
    )
    completed_time = fields.Datetime(
        string="离开时间",
        help="本道工序完成、件被交接走的时刻",
    )

    # 重量
    weight_in_g = fields.Float(
        string="接收重量 (g)",
        digits=(18, 6),
        help="件到达本工位时的重量",
    )
    weight_out_g = fields.Float(
        string="发出重量 (g)",
        digits=(18, 6),
        help="件完成本工序、交接出去时的重量",
    )
    weight_loss_g = fields.Float(
        string="本工序损耗 (g)",
        digits=(18, 6),
        compute="_compute_weight_loss",
        store=True,
    )

    # 状态
    state = fields.Selection(
        FLOW_CARD_STATE,
        string="状态",
        default="in_transit",
        required=True,
        tracking=True,
        index=True,
    )

    # 关联
    workorder_report_id = fields.Many2one(
        "gold.workorder.report",
        string="工序报工",
        help="本工序对应的报工记录",
    )
    qr_payload = fields.Char(
        string="交接二维码",
        help="扫码交接用的 QR 内容",
    )

    # 公司
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        default=lambda self: self.env.company,
    )
    note = fields.Text(string="备注")

    _sql_constraints = [
        # 同一件 SN 同时只能有一条 in_transit/at_station 状态的卡
        # 防止重复扫码(用 Python 约束,因为 SQL 写复杂条件)
    ]

    @api.depends("piece_id", "in_operation_id", "state")
    def _compute_display_name(self):
        for rec in self:
            sn = rec.piece_id.sn or "?"
            op = rec.in_operation_id.name or "?"
            rec.display_name = f"[{sn}] → {op}"

    @api.depends("weight_in_g", "weight_out_g")
    def _compute_weight_loss(self):
        for rec in self:
            if rec.weight_in_g and rec.weight_out_g:
                rec.weight_loss_g = max(0.0, rec.weight_in_g - rec.weight_out_g)
            else:
                rec.weight_loss_g = 0.0

    @api.constrains("piece_id", "in_operation_id")
    def _check_unique_in_transit(self):
        """同一 SN 同时只能有一条 in_transit 或 at_station 卡"""
        for rec in self:
            if rec.state in ("in_transit", "at_station"):
                duplicate = self.search([
                    ("id", "!=", rec.id),
                    ("piece_id", "=", rec.piece_id.id),
                    ("state", "in", ["in_transit", "at_station"]),
                ], limit=1)
                if duplicate:
                    raise ValidationError(
                        _("件级 SN %s 已有未完成的交接卡,需先关闭") % rec.piece_id.sn
                    )

    # ============================================================
    # 状态转换动作
    # ============================================================

    def action_confirm_received(self):
        """接收方扫码确认到达"""
        for rec in self:
            if rec.state != "in_transit":
                raise UserError(_("仅交接中状态可确认 (当前: %s)") % rec.state)
            rec.write({
                "state": "at_station",
                "received_time": fields.Datetime.now(),
                "receiver_id": self.env.user.id,
            })
            # 同步更新 SN 的当前位置
            rec.piece_id.write({
                "current_workstation_id": rec.in_workstation_id.id,
                "current_operation_id": rec.in_operation_id.id,
                "state": "in_process",
            })

    def action_complete(self, weight_out_g=None, workorder_report_id=None):
        """本工序完成,准备交接给下一道"""
        for rec in self:
            if rec.state != "at_station":
                raise UserError(_("仅工位上状态可完成 (当前: %s)") % rec.state)
            vals = {
                "state": "completed",
                "completed_time": fields.Datetime.now(),
            }
            if weight_out_g is not None:
                vals["weight_out_g"] = weight_out_g
            if workorder_report_id is not None:
                vals["workorder_report_id"] = workorder_report_id
            rec.write(vals)
            # 件仍算"在工位上"(等下一道扫码交接)

    def action_cancel(self, reason=None):
        """取消交接(误扫 / 退回)"""
        for rec in self:
            if rec.state == "completed":
                raise UserError(_("已完成的交接卡不能取消"))
            rec.write({
                "state": "cancelled",
                "note": (rec.note or "") + f"\n[取消] {reason or ''}",
            })

    # ============================================================
    # QR Payload
    # ============================================================

    @api.model
    def create(self, vals):
        if not vals.get("qr_payload") and vals.get("piece_id"):
            piece = self.env["gold.piece"].browse(vals["piece_id"])
            in_op = vals.get("in_operation_id")
            op_name = ""
            if in_op:
                op = self.env["gold.process.operation"].browse(in_op)
                op_name = op.code or op.name or ""
            vals["qr_payload"] = (
                f"https://handover.dunhuang-gold-mes.com/?sn={piece.sn}&op={op_name}"
            )
        return super().create(vals)

    # ============================================================
    # 追溯查询
    # ============================================================

    @api.model
    def get_piece_trace(self, sn):
        """根据 SN 查所有交接卡(完整旅程)"""
        piece = self.env["gold.piece"].search([("sn", "=", sn)], limit=1)
        if not piece:
            return {"found": False, "msg": f"SN {sn} 不存在"}
        cards = self.search([("piece_id", "=", piece.id)], order="handover_time asc")
        return {
            "found": True,
            "sn": piece.sn,
            "product": piece.product_id.display_name,
            "current_state": piece.state,
            "current_workstation": piece.current_workstation_id.name if piece.current_workstation_id else None,
            "current_operation": piece.current_operation_id.name if piece.current_operation_id else None,
            "flow_cards": [{
                "in_operation": c.in_operation_id.name,
                "out_operation": c.out_operation_id.name if c.out_operation_id else "(首道)",
                "in_workstation": c.in_workstation_id.name,
                "sender": c.sender_id.name,
                "receiver": c.receiver_id.name if c.receiver_id else None,
                "handover_time": str(c.handover_time) if c.handover_time else None,
                "received_time": str(c.received_time) if c.received_time else None,
                "completed_time": str(c.completed_time) if c.completed_time else None,
                "weight_in_g": c.weight_in_g,
                "weight_out_g": c.weight_out_g,
                "weight_loss_g": c.weight_loss_g,
                "state": c.state,
            } for c in cards],
        }