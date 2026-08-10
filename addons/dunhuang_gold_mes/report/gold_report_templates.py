# -*- coding: utf-8 -*-
"""
敦煌金加工车间 ERP — 报告模型
==========================

注册 PDF / HTML 报告:
  - 质量检验报告
  - XRF 含量检测报告
  - 工序报工汇总
  - 金料批次详情
  - 委外加工单
  - 损耗追溯报告

Odoo 17 通过 `ir.actions.report` 注册。
"""

from odoo import models, fields, api, _


class GoldReportMixin(models.AbstractModel):
    _name = "gold.report.mixin"
    _description = "贵金属报告通用方法"

    def _get_company_info(self):
        """取公司信息"""
        return self.env.company

    def _get_qr_payload(self, rec):
        """生成二维码内容(扫码追溯)"""
        if not rec:
            return ""
        return f"dunhuang-gold-mes://{self._name}/{rec.id}"


class GoldQualityReport(models.AbstractModel):
    _name = "report.dunhuang_gold_mes.quality_report"
    _description = "质量检验报告(QWeb)"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["gold.quality.inspection"].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": "gold.quality.inspection",
            "docs": docs,
            "company": self.env.company,
        }


class GoldXrfReport(models.AbstractModel):
    _name = "report.dunhuang_gold_mes.xrf_report"
    _description = "XRF 含量检测报告(QWeb)"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["gold.xrf.record"].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": "gold.xrf.record",
            "docs": docs,
            "company": self.env.company,
            "standard_thresholds": {
                "fine_gold": 99.00,
                "k18": 75.00,
                "k14": 58.50,
                "pt950": 95.00,
                "pd950": 95.00,
                "silver": 92.50,
            },
        }


class GoldBatchReport(models.AbstractModel):
    _name = "report.dunhuang_gold_mes.batch_report"
    _description = "金料批次详情报告(QWeb)"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["gold.material.batch"].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": "gold.material.batch",
            "docs": docs,
            "company": self.env.company,
        }


class GoldWorkorderReport(models.AbstractModel):
    _name = "report.dunhuang_gold_mes.workorder_summary"
    _description = "工序报工汇总报告(QWeb)"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["mrp.production"].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": "mrp.production",
            "docs": docs,
            "company": self.env.company,
            "report_lines": docs.gold_report_ids,
            "loss_traces": self.env["gold.loss.trace"].search(
                [("production_id", "in", docids)]
            ),
        }


class GoldOutsourceReport(models.AbstractModel):
    _name = "report.dunhuang_gold_mes.outsource_report"
    _description = "委外加工单报告(QWeb)"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["gold.outsource.order"].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": "gold.outsource.order",
            "docs": docs,
            "company": self.env.company,
        }


class GoldLossTraceReport(models.AbstractModel):
    _name = "report.dunhuang_gold_mes.loss_trace_report"
    _description = "损耗追溯报告(QWeb)"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["gold.loss.trace"].browse(docids)
        productions = docs.mapped("production_id")
        return {
            "doc_ids": docids,
            "doc_model": "gold.loss.trace",
            "docs": docs,
            "company": self.env.company,
            "productions": productions,
        }
