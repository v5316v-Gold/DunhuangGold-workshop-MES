/** @odoo-module **/
/*
 * 敦煌金加工车间 ERP — 看板 (OWL 组件)
 * 适用于 Odoo 17
 */

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";


export class GoldDashboard extends Component {
    static template = "gold_dashboard.Main";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this._loadData();
        this.interval = setInterval(() => this._loadData(), 30000);
    }

    willUnmount() {
        if (this.interval) {
            clearInterval(this.interval);
        }
    }

    async _loadData() {
        try {
            const [kpi, lossTrend, equipStatus] = await Promise.all([
                this.orm.call("gold.dashboard", "get_kpi", []),
                this.orm.call("gold.dashboard", "get_loss_trend", [7]),
                this.orm.call("gold.dashboard", "get_equipment_status", []),
            ]);
            this.data = {
                online: true,
                kpi,
                loss_trend: lossTrend,
                equip_status: equipStatus,
            };
            this.render();
        } catch (e) {
            console.error("看板数据加载失败", e);
            this.data = { online: false, kpi: {}, loss_trend: [] };
            this.render();
        }
    }

    onClickMold() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "gold.mold",
            views: [[false, "tree"], [false, "form"]],
        });
    }

    onClickLoss() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "gold.loss.trace",
            views: [[false, "tree"], [false, "form"]],
            domain: [["is_over_loss", "=", true]],
        });
    }
}

registry.category("actions").add("gold_dashboard.main", GoldDashboard);
