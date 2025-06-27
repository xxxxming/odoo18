# -*- coding: utf-8 -*-

from . import warehouse_property
from . import warehouse_information
from . import warehouse_automation
from . import warehouse_settings
from . import control_system
from . import control_system_operate
from . import frame_barcode
from . import warehouse_communication
from . import plc_connect


from .scheduler import PlcScheduler
import threading

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