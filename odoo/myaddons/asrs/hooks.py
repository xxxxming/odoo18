#-*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)

def my_post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    control_model = env['warehouse_communication']
    control_model.initialize_data()

    print('自动执行中')
    _logger.info("post_init_hook 已成功执行")

    # try:
    #     env = api.Environment(cr, SUPERUSER_ID, {})
    #     control_model = env['control.system.operate']
    #     if hasattr(control_model, 'initialize_data'):
    #         control_model.initialize_data()
    #     else:
    #         _logger.warning("control.system.operate 模型缺少 initialize_data 方法，跳过初始化")
    # except Exception as e:
    #     _logger.exception("post_init_hook 执行过程中发生异常: %s", str(e))
    #     raise
    # else:
    #     _logger.info("post_init_hook 已成功执行")