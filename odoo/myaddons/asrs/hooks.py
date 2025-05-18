#-*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)

def my_post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    control_model = env['control.system.operate']
    control_model.initialize_data()
    _logger.info("post_init_hook 已成功执行")