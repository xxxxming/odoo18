# -*- coding: utf-8 -*-

from . import plc_connect
from . import  warehouse_scheduler
from . import warehouse_automation
from . import warehouse_communication
from . import warehouse_control_system
from . import warehouse_frame_barcode
from . import  warehouse_property
from . import warehouse_settings
from . import warehouse_system_operate
from . import warehouse_location_information

from .warehouse_scheduler import PlcScheduler
import threading

import odoo
from odoo import api
import logging

plc_scheduler = PlcScheduler()

def _start_scheduler_once():
    def _thread():
        plc_scheduler.start()
    t = threading.Thread(target=_thread)
    t.setDaemon(True)
    t.start()

# 保证只启动一次（避免重复导入引发多个线程）
if not plc_scheduler.started:
    _start_scheduler_once()

# def _start_scheduler_once():
#     def _thread():
#         # 获取数据库名称
#         db_name = odoo.tools.config['db_name']
#         if db_name:
#             # 创建环境并传递给调度器
#             with odoo.sql_db.db_connect(db_name).cursor() as cr:
#                 env = api.Environment(cr, odoo.SUPERUSER_ID, {})
#                 plc_scheduler.start()
#         else:
#             _logger = logging.getLogger(__name__)
#             _logger.error("Database name not configured. Cannot start PLC scheduler.")
#             # 尝试不带env启动
#             plc_scheduler.start()
#
#     t = threading.Thread(target=_thread)
#     t.setDaemon(True)
#     t.start()
#
# # 保证只启动一次（避免重复导入引发多个线程）
# if not plc_scheduler.started:
#     _start_scheduler_once()