# -*- coding: utf-8 -*-
"""
贵金属车间 ERP — 金料批次
==========================

金料批次 = 物料 + 供应商 + 重量 + 含金量 + 实时价值 + 批次号。

批次规则:
  - GL-Au9999-20260805-001
  - 同一批次不可拆分,跨批次需移库
  - 重量精度 0.001g (NUMERIC 18,6)
  - 实时价 = weight * current_price
  - 移动加权平均法核算

数据类型:
  - 入库: 供应商来料 / 旧金回收 / 班后回料
  - 出库: 工艺投料 / 委外 / 调拨
  - 状态: draft / available / locked / consumed / depleted
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


BATCH_STATE_SELECTION = [
    ("draft", "草稿"),
    ("available", "可用"),
    ("locked", "锁定"),
    ("consumed", "已消耗"),
    ("depleted", "已耗尽"),
    ("scrap", "报废"),
]


BATCH_SOURCE_SELECTION = [
    ("supplier", "供应商来料"),
    ("recycle", "旧金回收"),
    ("internal", "内部调拨"),
    ("return", "工序回料"),
    ("rework", "返工回流"),
]


class GoldMaterialBatch(models.Model):
    _name = "gold.material.batch"
    _description = "金料批次"
    _order = "batch_no desc"
    _rec_name = "batch_no"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    batch_no = fields.Char(
        string="批次号",
        required=True,
        readonly=True,
        default=lambda self: _("新批次"),
        index=True,
    )
    name = fields.Char(
        string="批次名称",
        help="可选,用于备注",
    )
    # 物料
    product_id = fields.Many2one(
        "product.product",
        string="物料",
        required=True,
        domain="[('categ_id.gold_metal_type', '!=', '')]",
    )
    categ_id = fields.Many2one(
        related="product_id.categ_id",
        string="物料分类",
    )
    gold_metal_type = fields.Selection(
        related="product_id.categ_id.gold_metal_type",
        string="贵金属类型",
    )
    gold_purity = fields.Float(
        related="product_id.gold_purity",
        string="成色 (%)",
    )
    # 重量
    gross_weight_g = fields.Float(
        string="毛重 (g)",
        digits=(18, 6),
        required=True,
        default=0.0,
        help="批次总重量,精度 0.001g",
    )
    net_weight_g = fields.Float(
        string="净重 (g)",
        digits=(18, 6),
        required=True,
        default=0.0,
        help="扣除外包装/容器后的净重",
    )
    available_weight_g = fields.Float(
        string="可用重量 (g)",
        digits=(18, 6),
        default=0.0,
        help="净重 - 已分配 - 已消耗",
    )
    allocated_weight_g = fields.Float(
        string="已分配 (g)",
        digits=(18, 6),
        default=0.0,
    )
    consumed_weight_g = fields.Float(
        string="已消耗 (g)",
        digits=(18, 6),
        default=0.0,
    )
    # 来源
    source = fields.Selection(
        BATCH_SOURCE_SELECTION,
        string="来源",
        default="supplier",
        required=True,
    )
    supplier_id = fields.Many2one(
        "res.partner",
        string="供应商",
    )
    cert_no = fields.Char(
        string="检测证书号",
        help="供应商检测证书或回收料的化验证书",
    )
    # 检验
    inspection_state = fields.Selection(
        [
            ("pending", "待检"),
            ("passed", "合格"),
            ("failed", "不合格"),
        ],
        string="检验状态",
        default="pending",
        required=True,
    )
    inspector_id = fields.Many2one(
        "res.users",
        string="检验员",
    )
    inspection_date = fields.Datetime(string="检验时间")
    # 计价
    unit_price = fields.Float(
        string="入库单价 (元/g)",
        digits=(18, 4),
        default=0.0,
    )
    total_value = fields.Float(
        string="入库总价 (元)",
        digits=(18, 2),
        compute="_compute_total_value",
        store=True,
    )
    current_price = fields.Float(
        string="当前金价 (元/g)",
        digits=(18, 4),
        help="取自金价引擎,实时刷新",
    )
    current_value = fields.Float(
        string="当前价值 (元)",
        digits=(18, 2),
        compute="_compute_current_value",
        store=True,
    )
    # 状态
    state = fields.Selection(
        BATCH_STATE_SELECTION,
        string="状态",
        default="draft",
        required=True,
        tracking=True,
    )
    location_id = fields.Many2one(
        "stock.location",
        string="库存位置",
        help="金库 / 半成品库 / 不良品库",
    )
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        default=lambda self: self.env.company,
    )
    receive_date = fields.Date(
        string="入库日期",
        default=fields.Date.context_today,
    )
    # 旧金回收特属
    is_recycle = fields.Boolean(
        string="回收料",
        default=False,
    )
    recycle_order_id = fields.Many2one(
        "gold.recycle",
        string="回收单",
    )
    discount_factor = fields.Float(
        string="折价系数",
        digits=(6, 4),
        default=1.0,
        help="回收料折价系数,典型 0.95-0.98",
    )
    # 字段 - 平衡
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("batch_no_unique", "UNIQUE(batch_no, company_id)", "批次号必须唯一"),
        ("net_weight_positive", "CHECK(net_weight_g >= 0)", "净重必须 ≥ 0"),
        (
            "available_weight_positive",
            "CHECK(available_weight_g >= 0)",
            "可用重量必须 ≥ 0",
        ),
    ]

    @api.depends("net_weight_g", "unit_price")
    def _compute_total_value(self):
        for rec in self:
            rec.total_value = rec.net_weight_g * rec.unit_price

    @api.depends("available_weight_g", "current_price")
    def _compute_current_value(self):
        for rec in self:
            rec.current_value = rec.available_weight_g * rec.current_price

    @api.onchange("net_weight_g", "available_weight_g", "allocated_weight_g", "consumed_weight_g")
    def _onchange_weights(self):
        for rec in self:
            computed = (rec.net_weight_g or 0.0) - (rec.allocated_weight_g or 0.0) - (rec.consumed_weight_g or 0.0)
            if (rec.available_weight_g or 0.0) != computed:
                # 自动修正可用重量,但需提示
                rec.available_weight_g = computed

    @api.model
    def create(self, vals):
        if vals.get("batch_no", _("新批次")) == _("新批次"):
            vals["batch_no"] = self.env["ir.sequence"].next_by_code("gold.material.batch")
        rec = super().create(vals)
        # 初始可用 = 净重
        if rec.available_weight_g == 0.0:
            rec.available_weight_g = rec.net_weight_g
        return rec

    def action_available(self):
        """草稿 → 可用"""
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("仅草稿批次可入库"))
            if rec.net_weight_g <= 0:
                raise UserError(_("净重必须 > 0"))
            if rec.inspection_state != "passed":
                raise UserError(_("批次未通过检验,不可入库"))
            rec.state = "available"
            rec.available_weight_g = rec.net_weight_g

    def action_lock(self):
        """锁定批次(盘点 / 检验)"""
        for rec in self:
            if rec.state == "available":
                rec.state = "locked"

    def action_unlock(self):
        """解锁批次"""
        for rec in self:
            if rec.state == "locked":
                rec.state = "available"

    def action_scrap(self):
        """报废"""
        for rec in self:
            rec.state = "scrap"
            rec.available_weight_g = 0.0

    def allocate(self, weight_g):
        """分配指定重量,返回是否成功"""
        self.ensure_one()
        if self.state != "available":
            raise UserError(_("批次 %s 不可分配,当前状态: %s") % (self.batch_no, self.state))
        if weight_g > self.available_weight_g:
            raise UserError(
                _("批次 %s 可用重量不足:申请 %.3fg,可用 %.3fg")
                % (self.batch_no, weight_g, self.available_weight_g)
            )
        self.allocated_weight_g += weight_g
        self.available_weight_g -= weight_g
        return True

    def consume(self, weight_g):
        """实际消耗"""
        self.ensure_one()
        if weight_g > self.allocated_weight_g:
            raise UserError(
                _("批次 %s 分配不足:申请消耗 %.3fg,已分配 %.3fg")
                % (self.batch_no, weight_g, self.allocated_weight_g)
            )
        self.allocated_weight_g -= weight_g
        self.consumed_weight_g += weight_g
        if self.available_weight_g <= 0.0005 and self.allocated_weight_g <= 0.0005:
            self.state = "depleted"
        return True

    def release(self, weight_g):
        """释放已分配(取消订单/工艺回滚)"""
        self.ensure_one()
        if weight_g > self.allocated_weight_g:
            raise UserError(_("批次 %s 释放量超分配:%.3fg > %.3fg") % (self.batch_no, weight_g, self.allocated_weight_g))
        self.allocated_weight_g -= weight_g
        self.available_weight_g += weight_g
        if self.state == "depleted":
            self.state = "available"
        return True

    @api.constrains("net_weight_g", "available_weight_g", "allocated_weight_g", "consumed_weight_g")
    def _check_balance(self):
        for rec in self:
            total = (rec.allocated_weight_g or 0.0) + (rec.consumed_weight_g or 0.0) + (rec.available_weight_g or 0.0)
            diff = rec.net_weight_g - total
            if abs(diff) > 0.005:
                raise ValidationError(
                    _("批次 %s 重量不平衡:净重 %.3fg, (分配+消耗+可用) %.3fg, 差 %.3fg")
                    % (rec.batch_no, rec.net_weight_g, total, diff)
                )

    def name_get(self):
        result = []
        for rec in self:
            purity = "足金" if rec.gold_purity >= 99.0 else f"{rec.gold_purity:.2f}%"
            display = f"[{rec.batch_no}] {purity} {rec.net_weight_g:.3f}g"
            result.append((rec.id, display))
        return result
