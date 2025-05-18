odoo.define('plc_websocket.websocket', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var utils = require('web.utils');

    // WebSocket 客户端组件
    var PLCWebSocketClient = Widget.extend({
        template: 'PLCWebSocketClient',  // 对应 QWeb 模板的 ID
        ws: null,                        // WebSocket 实例
        reconnectInterval: 5000,         // 断线重连间隔（毫秒）
        maxRetries: 3,                   // 最大重试次数
        retryCount: 0,

        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.connectWebSocket();
        },

        connectWebSocket: function () {
            // WebSocket 连接配置
            const wsUrl = 'ws://localhost:8765';
            this.ws = new WebSocket(wsUrl);

            // 连接成功回调
            this.ws.onopen = () => {
                console.log('WebSocket 连接成功');
                this.retryCount = 0;  // 重置重试计数器
                this._sendInitialHandshake();
            };

            // 接收消息回调
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this._handleMessage(data);
            };

            // 错误处理
            this.ws.onerror = (error) => {
                console.error('WebSocket 错误:', error);
                this.ws.close();
            };

            // 连接关闭回调
            this.ws.onclose = (event) => {
                if (event.code !== 1000) {  // 非正常关闭
                    this._reconnect();
                }
            };
        },

        _sendInitialHandshake: function () {
            // 发送初始化握手消息（例如身份验证）
            const message = {
                action: 'auth',
                token: 'your_auth_token_here',  // 替换为实际认证令牌
            };
            this.ws.send(JSON.stringify(message));
        },

        _handleMessage: function (data) {
            // 处理不同类型的消息
            switch (data.type) {
                case 'plc_data':
                    this._updatePlcDisplay(data.payload);
                    break;
                case 'alert':
                    this._showAlert(data.message);
                    break;
                default:
                    console.warn('未知消息类型:', data.type);
            }
        },

        _updatePlcDisplay: function (payload) {
            // 更新界面上的 PLC 数据
            this.$el.find('.plc-value').text(payload.value);
            this.$el.find('.plc-timestamp').text(payload.timestamp);
        },

        _showAlert: function (message) {
            // 显示警报通知
            core.bus.trigger('show_notification', {
                type: 'danger',
                message: message,
                sticky: true,
            });
        },

        _reconnect: function () {
            // 断线自动重连
            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                console.log(`尝试第 ${this.retryCount} 次重连...`);
                setTimeout(() => this.connectWebSocket(), this.reconnectInterval);
            } else {
                this._showAlert('无法连接至实时服务器');
            }
        },

        destroy: function () {
            // 清理资源
            if (this.ws) {
                this.ws.close();
            }
            this._super.apply(this, arguments);
        },
    });

    // 注册组件至 Odoo 界面
    core.action_registry.add('plc_websocket_client', PLCWebSocketClient);

    return {
        PLCWebSocketClient: PLCWebSocketClient,
    };
});