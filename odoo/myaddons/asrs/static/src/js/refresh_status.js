/** @odoo-module **/
import { Field } from "@web/views/fields/field";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";


class RefreshStorageFields extends Field {
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
        const data = await rpc("/asrs/refresh_status", { record_id: recordId });
        console.log('refresh_status', data['refresh_status']);
        if (data && data['refresh_status'] === true) {  // 判断 statu_code 是否为真
//            增加刷新字段
            for (const field of ['allow_store','allow_outbound','allow_return','pack_barcode','location_number','source_target', 'new_target']) {
                if (data[field] !== undefined) {
                    this.props.record.data[field] = data[field];
                }
            }
                this.update();
            } else {
                console.log('statut_code 为 false，跳过刷新');
            }
        } catch (e) {
        }
    }, 1000);

    }
    willUnmount() {
        clearInterval(this.timer);
        super.willUnmount?.();
    }
    render() {
        return this.value === undefined ? '' : String(this.value);
    }
}
registry.category("fields").add("RefreshStorageFields", {
    component: RefreshStorageFields,
    supportedTypes: ["char", "integer"],
});
