# -*- coding: utf-8 -*-

from . import plc_connect
# from . import  warehouse_scheduler
from . import warehouse_plc_task
from . import warehouse_automation
from . import warehouse_communication
from . import warehouse_control_system
from . import warehouse_frame_barcode
from . import  warehouse_property
from . import warehouse_settings
from . import warehouse_system_operate
from . import warehouse_location_information

# from .warehouse_scheduler import PlcScheduler
import threading

import odoo
from odoo import api
import logging

# plc_scheduler = PlcScheduler()
#
# def _start_scheduler_once():
#     def _thread():
#         plc_scheduler.start()
#     t = threading.Thread(target=_thread)
#     t.setDaemon(True)
#     t.start()
#
# # 保证只启动一次（避免重复导入引发多个线程）
# if not plc_scheduler.started:
#     _start_scheduler_once()
