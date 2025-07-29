/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";

class CustomSelectorDialog extends Component {
    static template = "asrs.CustomSelectorDialog";
    static props = {
        close: Function,
        confirm: Function,
        data: { type: Array, optional: true },
        selectedValue: { type: String, optional: true },
    };
    static components = { Dialog };

    setup() {
        this.state = useState({
            selectedValue: this.props.selectedValue || "",
        });
    }

    onSelectValue(ev, value) {
        ev.stopPropagation();
        this.state.selectedValue = value;
    }

    onConfirm() {
        this.props.confirm(this.state.selectedValue);
    }
}

export class CustomSelectorField extends Component {
    static template = "asrs.CustomSelectorField";
    static props = {
        value: { type: String, optional: true },
        update: { type: Function, optional: true },
        readonly: { type: Boolean, optional: true },
        record: { type: Object, optional: true },
    };

    setup() {
        this.dialogService = useService("dialog");
    }

    onClick(ev) {
        if (this.props.readonly) {
            return;
        }

        // 这里可以定义你的自定义数据
        const selectorData = [
            { id: 1, name: "选项 1" },
            { id: 2, name: "选项 2" },
            { id: 3, name: "选项 3" },
            { id: 4, name: "选项 4" },
            { id: 5, name: "选项 5" },
        ];

        this.dialogService.add(CustomSelectorDialog, {
            data: selectorData,
            selectedValue: this.props.value || "",
            confirm: (value) => {
                // 设置选中的值
                if (this.props.update) {
                    this.props.update(value);
                }
            },
        });
    }
}

// 注册widget
registry.category("new_target").add("custom_selector", CustomSelectorField);
