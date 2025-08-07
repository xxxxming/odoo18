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

# 在文件末尾添加自动启动代码
def start_scheduler_on_boot():
    """在Odoo启动时自动启动调度器"""
    import time
    time.sleep(10)  # 等待Odoo完全启动

    try:
        # 连接到数据库
        db_name = odoo.tools.config['db_name']
        if not db_name:
            db_name = 'odoo18e'  # 默认数据库名

        with odoo.sql_db.db_connect(db_name).cursor() as cr:
            env = api.Environment(cr, odoo.SUPERUSER_ID, {})
            plc_task_model = env['warehouse.plc.task']
            plc_task_model.start_scheduler()
            logging.getLogger(__name__).info("scheduled task start follow system !")
    except Exception as e:
        logging.getLogger(__name__).exception("scheduled task start fault : %s", str(e))


# 启动后台线程
threading.Thread(target=start_scheduler_on_boot, daemon=True).start()