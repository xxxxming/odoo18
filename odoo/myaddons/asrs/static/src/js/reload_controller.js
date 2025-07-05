   import { Component, useEffect } from "@odoo/owl";
   import { registry } from "@web/core/registry";

//   class ReloadController extends Component {
//       static template = "CustomModelReloader";
//
//       setup() {
//           // 总线消息监听
//           this.env.bus.on(`model_reload_${this.props.recordId}`, () => {
//               this._reloadData();
//           });
//
//           // 轮询备份
//           useEffect((interval) => {
//               const timer = setInterval(() => {
//                   if (this.props.autoReload) this._reloadData();
//               }, interval * 1000);
//               return () => clearInterval(timer);
//           }, () => [this.props.reloadInterval || 2]);
//       }
//
//       async _reloadData() {
//           await this.env.services.rpc("/web/dataset/call_kw", {
//               model: this.props.model,
//               method: "read",
//               args: [[this.props.recordId], ["name", "state"]],
//               kwargs: { context: this.env.session.user_context }
//           });
//       }
//   }
//
//   registry.category("views").add("reload_controller", ReloadController);


oo.define('custom.ReloadController', function (require) {
"use strict";

const { Component } = owl;
const { useListener } = require('web.custom_hooks');

class ReloadController extends Component {
    setup() {
        this.lastState = false;
        useListener('single_reload', this._onReload);
    }

    _onReload() {
        if (this.props.record.data.need_reload && !this.lastState) {
            this.props.record.load();
        }
        this.lastState = this.props.record.data.need_reload;
    }
}

return ReloadController;
});





















