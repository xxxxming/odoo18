/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useModel } from "@web/model/model";

export class RefreshBaseNumber extends Component {
    setup() {
        console.log("✅ [setup] RefreshBaseNumber 组件 setup() 开始执行");
        this.model = useModel();
        this.state = useState({ value: "" });

        onMounted(() => {
            console.log("✅ [onMounted] 组件挂载完成，开始轮询");

            this.fetchValue();  // 首次立即拉取
            this.interval = setInterval(() => {
                console.log("⏱️ [Interval] 定时器触发，准备刷新字段值");
                this.fetchValue();
            }, 5000);
        });
    }

    async fetchValue() {
        const resId = this.model.root.resId;
        console.log("🔍 [fetchValue] 正在请求字段值，resId =", resId);

        try {
            const result = await this.rpc("/web/dataset/call_kw", {
                model: "control.system.operate",
                method: "read",
                args: [[resId], ["storage_base_number"]],
                kwargs: {},
            });
            this.state.value = result?.[0]?.storage_base_number || "";
            console.log("✅ [fetchValue] 获取成功，值 =", this.state.value);
        } catch (err) {
            console.error("❌ [fetchValue] 请求失败", err);
        }
    }

    willUnmount() {
        console.log("🛑 [willUnmount] 组件即将销毁，清除定时器");
        clearInterval(this.interval);
    }
}

RefreshBaseNumber.template = "asrs.RefreshBaseNumber";
registry.category("view_components").add("refresh_base_number", RefreshBaseNumber);
