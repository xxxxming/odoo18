/** @odoo-module **/

import { busService } from "@bus/services/bus_service";
import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";
import { onWillStart, onMounted, onWillUnmount } from "@odoo/owl";

console.log('=== Warehouse Bus Sync Module Loading ===');

// 扩展表单控制器以处理实时更新
export class WarehouseFormController extends FormController {
    setup() {
        console.log('=== WarehouseFormController.setup() called ===');
        super.setup();
        console.log('Base FormController setup completed');
        try {
            this.busService = useService("bus_service");
            console.log('Bus service acquired successfully:', !!this.busService);
        } catch (error) {
            console.error('Failed to acquire bus service:', error);
            return;
        }

        // 根据模型类型订阅相应频道
        onWillStart(async () => {
            console.log('=== onWillStart executed ===');
            console.log('Current resModel:', this.props.resModel);
            const busService = this.env.services.bus_service;
            if (this.props.resModel === 'warehouse.system.operate') {
                this.busService.addChannel('warehouse_data_update');
                console.log('Channel warehouse_data_update added');
            } else if (this.props.resModel === 'warehouse.control.system') {
                this.busService.addChannel('warehouse_control_update');
                console.log('Channel warehouse_control_update added');
            }
        });

//        // 监听通知
//        onMounted(() => {
//            console.log('Adding notification listener for:', this.props.resModel);
//            if (this.props.resModel === 'warehouse.system.operate' ||
//                this.props.resModel === 'warehouse.control.system') {
//                console.log('Adding notification listener');
//
//                // 监听所有通知
//                const allNotificationsHandler = (event) => {
//                    console.log('ALL NOTIFICATIONS:', event);
//                };
//                this.busService.addEventListener("*", allNotificationsHandler);
//
//                console.log('Adding all notification listener');
//                this.busService.addEventListener("notification", this.onNotification.bind(this));
//                console.log('Notification listener added successfully');
//            }
//            console.log('=== onMounted completed ===');
//        });

        onMounted(() => {
            console.log('=== onMounted executed ===');
            console.log('Current resModel:', this.props.resModel);
            if (this.props.resModel === 'warehouse.system.operate' ||
                this.props.resModel === 'warehouse.control.system') {

                // 使用 subscribe 方法而不是 addEventListener
                const handleWarehouseDataUpdate = (payload, metadata) => {
                    console.log('=== WAREHOUSE DATA UPDATE RECEIVED (via subscribe) ===');
                    console.log('Payload:', payload);
                    console.log('Metadata:', metadata);

                    // 处理接收到的数据
                    if (this.props.resModel === 'warehouse.system.operate') {
                        this.handleDataUpdate(payload);
                    }
                };

                const handleWarehouseControlUpdate = (payload, metadata) => {
                    console.log('=== WAREHOUSE CONTROL UPDATE RECEIVED (via subscribe) ===');
                    console.log('Payload:', payload);
                    console.log('Metadata:', metadata);

                    // 处理接收到的数据
                    if (this.props.resModel === 'warehouse.control.system') {
                        this.handleControlUpdate(payload);
                    }
                };

                this.busService.subscribe('warehouse.data_update', handleWarehouseDataUpdate);
                this.busService.subscribe('warehouse.control_update', handleWarehouseControlUpdate);
                console.log('Subscribed to warehouse update events');
            }
            console.log('=== onMounted completed ===');
        });

        // 清理订阅
        onWillUnmount(() => {
             const busService = this.env.services.bus_service;
            if (this.props.resModel === 'warehouse.system.operate') {
                console.log('Removing channel: warehouse_data_update');
                this.busService.deleteChannel('warehouse_data_update');
            } else if (this.props.resModel === 'warehouse.control.system') {
                console.log('Removing channel: warehouse_control_update');
                this.busService.deleteChannel('warehouse_control_update');
            }
            this.busService.removeEventListener("notification", this.onNotification.bind(this));
        });
    }

    onNotification({ detail: notifications }) {
         console.log('Processing warehouse notifications in form:', notifications);
        // 处理通知的逻
        for (const notification of notifications) {
            if (notification.type === 'warehouse.data_update' &&
                this.props.resModel === 'warehouse.system.operate') {
                this.handleDataUpdate(notification.payload);
            } else if (notification.type === 'warehouse.control_update' &&
                this.props.resModel === 'warehouse.control.system') {
                this.handleControlUpdate(notification.payload);
            }
        }
    }

//    refreshSpecificFields(updatedFields) {
//        console.log('Refreshing specific fields:', updatedFields);
//
//        // 方法1: 触发字段更新事件
//        updatedFields.forEach(updatedFields => {
//            if (this.model.root.bus) {
//                this.model.root.bus.trigger(`refresh-field:${updatedFields}`);
//            }
//        });
//
//        // 方法2: 如果有渲染器，尝试刷新特定字段
//        if (this.renderer && this.renderer.fields) {
//            updatedFields.forEach(updatedFields => {
//                if (this.renderer.fields[updatedFields]) {
//                    try {
//                        if (typeof this.renderer.fields[updatedFields].render === 'function') {
//                            this.renderer.fields[updatedFields].render();
//                            console.log(`Field ${updatedFields} re-rendered`);
//                        }
//                    } catch (error) {
//                        console.warn(`Error refreshing field ${updatedFields}:`, error);
//                    }
//                }
//            });
//        }
//    }

    async handleDataUpdate(data) {
        console.log('Handling data update in form:', data);

//        const record = this.model.root.records.find(rec => rec.resId === data.id);
//        if (record) {
//            record.update(data.changed_fields);
//
//        }

         await this.model.root.update(data.changed_fields);

        // 刷新指定字段
//        const updatedFields = Object.keys(data.changed_fields);
//        console.log('Change fields:', updatedFields);
//        this.refreshSpecificFields(updatedFields);



    }

    async handleControlUpdate(data) {
        console.log('Handling data update in list:', data);

        await this.model.root.update(data.changed_fields);

//        const record = this.model.root.records.find(rec => rec.resId === data.id);
//        if (record) {
//            record.update(data.changed_fields);
//        }



    }
}
console.log("Warehouse bus sync extension loaded successfully");


// 扩展列表控制器以处理列表视图中的实时更新
export class WarehouseListController extends ListController {
    setup() {
        console.log('=== WarehouseListController.setup() called ===');
        super.setup();
        console.log('Base ListController setup completed');
        this.busService = useService("bus_service");

        // 订阅频道
        onWillStart(async () => {
            if (this.props.resModel === 'warehouse.system.operate') {
                this.busService.addChannel('warehouse_data_update');
                console.log('Channel warehouse_data_update added in list view');
            } else if (this.props.resModel === 'warehouse.control.system') {
                this.busService.addChannel('warehouse_control_update');
                 console.log('Channel warehouse_control_update added in list view');
            }
        });

        // 监听通知
        onMounted(() => {
            console.log('Adding list notification listener for:', this.props.resModel);
            const busService = this.env.services.bus_service;
            if (this.props.resModel === 'warehouse.system.operate' ||
                this.props.resModel === 'warehouse.control.system') {
                console.log('Adding notification listener in list view');
                this.busService.addEventListener("notification", this.onNotification.bind(this));
            }
        });

        // 清理订阅
        onWillUnmount(() => {
            const busService = this.env.services.bus_service;
            if (this.props.resModel === 'warehouse.system.operate') {
                console.log('Removing list channel: warehouse_data_update');
                this.busService.deleteChannel('warehouse_data_update');
            } else if (this.props.resModel === 'warehouse.control.system') {
                console.log('Removing list channel: warehouse_control_update');
                this.busService.deleteChannel('warehouse_control_update');
            }
            this.busService.removeEventListener("notification", this.onNotification.bind(this));
        });
    }

    onNotification({ detail: notifications }) {
        console.log('Processing warehouse notifications in list:', notifications);
        for (const notification of notifications) {
            if ((notification.type === 'warehouse.data_update' &&
                 this.props.resModel === 'warehouse.system.operate') ||
                (notification.type === 'warehouse.control_update' &&
                 this.props.resModel === 'warehouse.control.system')) {
                this.handleListUpdate(notification.payload);
            }
        }
    }


    handleListUpdate(data) {
        console.log('Handling list update:', data);
        // 查找并更新列表中的记录
//        const record = this.model.root.records.find(rec => rec.resId === data.id);
//        if (record) {
//            record.update(data.changed_fields);
//
//        }

    }
}

console.log("Warehouse bus sync extension loaded successfully");

//// 在文件末尾添加代码来扩展现有的表单控制器
//import { patch } from "@web/core/utils/patch";
//import { useService } from "@web/core/utils/hooks";
//import { onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
//
//// 扩展标准的 FormController
//patch(FormController.prototype, "asrs.WarehouseBusSync", {
//    setup() {
//        super.setup();
//        console.log("Patched FormController setup for warehouse models");
//
//        // 只对特定模型应用扩展
//        if (this.props.resModel === 'warehouse.system.operate' ||
//            this.props.resModel === 'warehouse.control.system') {
//
//            this.busService = useService("bus_service");
//
//            // 添加频道
//            onWillStart(async () => {
//                if (this.props.resModel === 'warehouse.system.operate') {
//                    console.log('Adding warehouse_data_update channel');
//                    this.busService.addChannel('warehouse_data_update');
//                } else if (this.props.resModel === 'warehouse.control.system') {
//                    console.log('Adding warehouse_control_update channel');
//                    this.busService.addChannel('warehouse_control_update');
//                }
//            });
//
//            // 监听通知
//            onMounted(() => {
//                console.log('Adding notification listener');
//                this.busService.addEventListener("notification", (notifications) => {
//                    console.log('Received notifications:', notifications);
//                    this._onWarehouseNotification(notifications);
//                });
//            });
//
//            // 清理
//            onWillUnmount(() => {
//                if (this.props.resModel === 'warehouse.system.operate') {
//                    console.log('Removing warehouse_data_update channel');
//                    this.busService.deleteChannel('warehouse_data_update');
//                } else if (this.props.resModel === 'warehouse.control.system') {
//                    console.log('Removing warehouse_control_update channel');
//                    this.busService.deleteChannel('warehouse_control_update');
//                }
//                console.log('Removing notification listener');
//            });
//        }
//    },
//
//    _onWarehouseNotification(notifications) {
//        console.log('Processing warehouse notifications:', notifications);
//        // 处理通知的逻辑
//        for (const notification of notifications.detail) {
//            if (notification.type === 'warehouse.data_update' &&
//                this.props.resModel === 'warehouse.system.operate') {
//                this._handleDataUpdate(notification.payload);
//            } else if (notification.type === 'warehouse.control_update' &&
//                this.props.resModel === 'warehouse.control.system') {
//                this._handleControlUpdate(notification.payload);
//            }
//        }
//    },
//
//    async _handleDataUpdate(data) {
//        console.log('Handling data update:', data);
//        // 确保是当前记录的更新
//        if (this.model.root.data.id === data.id) {
//            // 更新记录
//            await this.model.root.update(data.changed_fields);
//        }
//    },
//
//    async _handleControlUpdate(data) {
//        console.log('Handling control update:', data);
//        // 确保是当前记录的更新
//        if (this.model.root.data.id === data.id) {
//            // 更新记录
//            await this.model.root.update(data.changed_fields);
//        }
//    }
//});
//
//console.log("Warehouse bus sync extension loaded");



// 注册扩展的控制器

registry.category("views").add("warehouse_form", {
    ...formView,
    Controller: WarehouseFormController,
});

registry.category("views").add("warehouse_list", {
    ...listView,
    Controller: WarehouseListController,
});


//// 添加一个简单的测试函数来验证基本功能
//function testBasicFunctionality() {
//    console.log('=== Warehouse Bus Sync Test ===');
//    console.log('Module loaded successfully');
//
//    // 检查必要的导入是否成功
//    if (typeof FormController !== 'undefined') {
//        console.log('FormController imported successfully');
//    } else {
//        console.error('FormController import failed');
//    }
//
//    if (typeof useService !== 'undefined') {
//        console.log('useService imported successfully');
//    } else {
//        console.error('useService import failed');
//    }
//
//    if (typeof registry !== 'undefined') {
//        console.log('registry imported successfully');
//    } else {
//        console.error('registry import failed');
//    }
//}
//
//// 立即执行测试
//testBasicFunctionality();







//odoo.define('asrs.WarehouseBusSync', function (require) {
//    "use strict";
//
//    var core = require('web.core');
//    var BusService = require('bus.BusService');
//    var FormController = require('web.FormController');
//    var ListRenderer = require('web.ListRenderer');
//
//    var _t = core._t;
//
//    // 扩展表单控制器以处理实时更新
//    FormController.include({
//        init: function (parent, model, renderer, params) {
//            this._super.apply(this, arguments);
//
//            // 订阅频道
//            this.warehouseDataChannel = 'warehouse_data_update';
//            this.warehouseControlChannel = 'warehouse_control_update';
//        },
//
//        willStart: function () {
//            var self = this;
//            return this._super.apply(this, arguments).then(function () {
//                // 根据模型类型订阅相应频道
//                if (self.modelName === 'warehouse.system.operate') {
//                    self.call('bus_service', 'addChannel', self.warehouseDataChannel);
//                } else if (self.modelName === 'warehouse.control.system') {
//                    self.call('bus_service', 'addChannel', self.warehouseControlChannel);
//                }
//            });
//        },
//
//        start: function () {
//            var self = this;
//            return this._super.apply(this, arguments).then(function () {
//                // 监听通知
//                if (self.modelName === 'warehouse.system.operate' ||
//                    self.modelName === 'warehouse.control.system') {
//                    self.call('bus_service', 'onNotification', self, self._onNotification);
//                }
//            });
//        },
//
//        _onNotification: function (notifications) {
//            var self = this;
//            _.each(notifications, function (notification) {
//                if (notification.type === 'warehouse.data_update' &&
//                    self.modelName === 'warehouse.system.operate') {
//                    self._handleDataUpdate(notification.payload);
//                } else if (notification.type === 'warehouse.control_update' &&
//                    self.modelName === 'warehouse.control.system') {
//                    self._handleControlUpdate(notification.payload);
//                }
//            });
//        },
//
//        /**
//         * 处理warehouse.system.operate模型的数据更新
//         */
//        _handleDataUpdate: function (data) {
//            var self = this;
//
//            // 确保是当前记录的更新
//            if (this.handle && this.renderer.state &&
//                this.renderer.state.res_id === data.id) {
//
//                // 更新记录
//                this.modelPointier.updateRecord(this.handle, data.changed_fields)
//                    .then(function () {
//                        // 通知渲染器更新界面
//                        self.renderer.confirmChange(
//                            self.renderer.state,
//                            self.handle,
//                            Object.keys(data.changed_fields)
//                        );
//                    });
//            }
//        },
//
//        /**
//         * 处理warehouse.control.system模型的控制状态更新
//         */
//        _handleControlUpdate: function (data) {
//            var self = this;
//
//            // 确保是当前记录的更新
//            if (this.handle && this.renderer.state &&
//                this.renderer.state.res_id === data.id) {
//
//                // 更新记录
//                this.modelPointier.updateRecord(this.handle, data.changed_fields)
//                    .then(function () {
//                        // 通知渲染器更新界面
//                        self.renderer.confirmChange(
//                            self.renderer.state,
//                            self.handle,
//                            Object.keys(data.changed_fields)
//                        );
//                    });
//            }
//        },
//
//        destroy: function () {
//            // 清理订阅
//            if (this.modelName === 'warehouse.system.operate') {
//                this.call('bus_service', 'deleteChannel', this.warehouseDataChannel);
//            } else if (this.modelName === 'warehouse.control.system') {
//                this.call('bus_service', 'deleteChannel', this.warehouseControlChannel);
//            }
//            this._super.apply(this, arguments);
//        }
//    });
//
//    // 扩展列表渲染器以处理列表视图中的实时更新
//    ListRenderer.include({
//        init: function (parent, state, params) {
//            this._super.apply(this, arguments);
//
//            // 监听相关模型的更新
//            this.supportedModels = [
//                'warehouse.system.operate',
//                'warehouse.control.system'
//            ];
//        },
//
//        willStart: function () {
//            var self = this;
//            return this._super.apply(this, arguments).then(function () {
//                // 如果是支持的模型，订阅频道
//                if (self.state &&
//                    self.supportedModels.includes(self.state.model)) {
//
//                    if (self.state.model === 'warehouse.system.operate') {
//                        self.call('bus_service', 'addChannel', 'warehouse_data_update');
//                    } else if (self.state.model === 'warehouse.control.system') {
//                        self.call('bus_service', 'addChannel', 'warehouse_control_update');
//                    }
//                }
//            });
//        },
//
//        start: function () {
//            var self = this;
//            return this._super.apply(this, arguments).then(function () {
//                // 监听通知
//                if (self.state &&
//                    self.supportedModels.includes(self.state.model)) {
//                    self.call('bus_service', 'onNotification', self, self._onNotification);
//                }
//            });
//        },
//
//        _onNotification: function (notifications) {
//            var self = this;
//            _.each(notifications, function (notification) {
//                if ((notification.type === 'warehouse.data_update' &&
//                     self.state.model === 'warehouse.system.operate') ||
//                    (notification.type === 'warehouse.control_update' &&
//                     self.state.model === 'warehouse.control.system')) {
//                    self._handleListUpdate(notification.payload);
//                }
//            });
//        },
//
//        /**
//         * 处理列表视图中的更新
//         */
//        _handleListUpdate: function (data) {
//            var self = this;
//
//            // 查找更新的记录是否在当前列表中
//            var record = _.find(this.state.data, function (rec) {
//                return rec.id === data.id;
//            });
//
//            if (record) {
//                // 更新记录数据
//                _.each(data.changed_fields, function (value, fieldName) {
//                    record.data[fieldName] = value;
//                });
//
//                // 重新渲染相关行
//                this._renderRow(record);
//            }
//        },
//
//        /**
//         * 重新渲染指定行
//         */
//        _renderRow: function (record) {
//            // 找到对应的行元素
//            var $row = this.$('.o_data_row[data-id="' + record.id + '"]');
//            if ($row.length) {
//                // 重新渲染行
//                this._renderRowField($row, record);
//            }
//        },
//
//        /**
//         * 重新渲染行中的字段
//         */
//        _renderRowField: function ($row, record) {
//            // 触发重新渲染
//            this._render();
//        },
//
//        destroy: function () {
//            // 清理订阅
//            if (this.state &&
//                this.supportedModels.includes(this.state.model)) {
//
//                if (this.state.model === 'warehouse.system.operate') {
//                    this.call('bus_service', 'deleteChannel', 'warehouse_data_update');
//                } else if (this.state.model === 'warehouse.control.system') {
//                    this.call('bus_service', 'deleteChannel', 'warehouse_control_update');
//                }
//            }
//            this._super.apply(this, arguments);
//        }
//    });
//
//    return {
//        FormController: FormController,
//        ListRenderer: ListRenderer
//    };
//});
