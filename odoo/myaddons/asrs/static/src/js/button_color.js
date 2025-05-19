/** @odoo-module **/



odoo.define('asrs.button_color', function (require) {
    "use strict";

    const FormController = require('web.FormController');

    FormController.include({
        _updateButtons: function () {
            this._super.apply(this, arguments);

            // 找到按钮
            const $btn = this.$buttons.find('.btn_color_toggle');
            if (!$btn.length) return;

            // 获取当前记录的数据
            const data = this.model.get(this.handle).data;
            if (!data) return;
            console.log('data', data.emergency_stop);
            // 根据字段 emergency_stop 设置按钮颜色
          if (data.emergency_stop === true) {
                $btn.css({'background-color': 'green', 'color': 'white'});
            } else if (data.emergency_stop === false) {
                $btn.css({'background-color': 'red', 'color': 'white'});
            } else {
                // 如果是 undefined 或 null，给个默认颜色，方便排查
                $btn.css({'background-color': 'gray', 'color': 'white'});
            }


        },
    });
});


