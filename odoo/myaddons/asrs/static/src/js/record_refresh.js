odoo.define('control_system_operation.RecordRefreshManager', function (require) {
    "use strict";

    var AbstractController = require('web.AbstractController');
    var bus = require('bus.bus');
    var core = require('web.core');
    var session = require('web.session');

    var _t = core._t;

    AbstractController.include({
        custom_events: _.extend({}, AbstractController.prototype.custom_events || {}, {
            'record_refresh': '_onRecordRefresh',
        }),

        init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
            this.dbname = session.db;
            this.modelName = params.modelName;
            this.resID = params.activeIds && params.activeIds[0];
            this._setupBusListening();
        },

        _setupBusListening: function() {
            if (!this.resID) return;

            // 生成特定记录频道
            this.recordChannel = `${this.modelName}.record.refresh.${this.resID}`;

            // 监听总线通知
            bus.on('notification', this, this._onBusNotification);

            // 注册频道
            bus.add_channel(this.recordChannel);
        },

        console.log("Listening to channel:", this.recordChannel);

        _onBusNotification: function(notifications) {
            var self = this;
            _.each(notifications, function(notification) {
                if (notification[0][1] === 'record_refresh' &&
                    notification[1].model === self.modelName &&
                    notification[1].record_id === self.resID) {
                    self.trigger('record_refresh', notification[1]);
                }
            });
        },

        _onRecordRefresh: function(event) {
            event.stopPropagation();
            this._refreshRecordData();
        },

        _refreshRecordData: function() {
            var self = this;

            // 1. 获取当前视图中所有可见字段
            var fields = this.renderer.state.fields;
            var fieldNames = _.keys(fields);

            // 2. 使用read方法获取最新数据
            this.model.read(this.handle, fieldNames)
                .then(function(data) {
                    if (!data || !data.length) return;

                    // 3. 静默更新模型数据（不触发完整渲染）
                    self.model.set(self.handle, data[0], {
                        silent: true  // 避免触发不必要的事件
                    });

                    // 4. 只更新变更的字段
                    return self.renderer.updateState(data[0], {
                        noRender: true,  // 不执行完整渲染
                        notifyChange: false  // 不通知变更
                    });
                })
                .then(function() {
                    // 可选：显示刷新成功的通知
                    self.do_notify(_t("Success"), _t("Data has been refreshed"));
                })
                .catch(function(error) {
                    console.error("Record refresh error:", error);
                    self.do_warn(_t("Error"), _t("Failed to refresh data"));
                });
        },

        destroy: function() {
            if (this.recordChannel) {
                bus.delete_channel(this.recordChannel);
            }
            this._super.apply(this, arguments);
        }
    });
});