/** @odoo-module **/
import { Field } from "@web/views/fields/field";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

class RefreshFullModel extends Field {
    setup() {
        super.setup();
        this.value = this.props.value;
        this.startRefreshing();
    }

    startRefreshing() {
        const recordId = this.props.record.resId;
        if (!recordId) return;

        this.timer = setInterval(async () => {
            try {
                const data = await rpc("/asrs/full_model_refresh", { record_id: recordId });
                if (data && data['statut_code'] === true) {
                    for (const [field, value] of Object.entries(data)) {
                        if (field !== 'statut_code') {
                            this.props.record.data[field] = value;
                        }
                    }
                    this.update();
                }
            } catch (e) {
                console.warn("🔥 刷新失败:", e);
            }
        }, 3000);
    }

    willUnmount() {
        clearInterval(this.timer);
        super.willUnmount?.();
    }

    render() {
        return this.value === undefined ? '' : String(this.props.record.data[this.props.name]);
    }
}

registry.category("fields").add("RefreshFullModel", {
    component: RefreshFullModel,
    supportedTypes: ["char", "integer"],
});
