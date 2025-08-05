import time
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from .warehouse_communication import New_Public_PlcInterfaces
import odoo
from odoo import api
_logger = logging.getLogger(__name__)

class PlcScheduler():

    _name = 'warehouse_scheduler'
    _description = 'warehouse scheduler'

    def __init__(self):
        self.env = None
        self.scheduler = BackgroundScheduler()
        self.started = False
        self.one_second = 0
        self.one_minute = 0

    def start(self):
        """
        启动调度器，初始化定时任务。
        如果调度器未启动，则添加每100秒执行一次的one_second_task任务，
        并启动调度器。
        """

        if not self.started:
            _logger.info("🚀 启动 PLC 调度器")
            # 添加间隔任务：每1秒调用一次 one_second_task 方法
            self.scheduler.add_job(self.scheduled_tasks, 'interval', seconds=2, max_instances=4)
            # #添加间隔任务：每1秒调用一次 one_second_task 方法
            # self.scheduler.add_job(self.one_second_task, 'interval', seconds=2, max_instances=4)
            # # 添加间隔任务：每10秒调用一次 one_second_task 方法
            # self.scheduler.add_job(self.ten_second_task, 'interval', seconds=5, max_instances=4)
            # 启动后台调度器
            self.scheduler.start()
            self.started = True

    def scheduled_tasks(self):
        start_time = time.time()
        db_name = 'odoo18e'  # ← 修改为你自己的数据库名
        with odoo.sql_db.db_connect(db_name).cursor() as cr:
            env = api.Environment(cr, 1, {})  # 1 表示超级管理员 user_id
        try:
            # 调用 New_Public_PlcInterfaces 类的 one_second_task 方法
            result = New_Public_PlcInterfaces(env)
            result.one_second_task()
            if self.one_second == 9:
                result.ten_second_task()
            self.one_second = (self.one_second + 1) % 10
            self.one_minute = (self.one_minute + 1) % 60
            if self.one_minute == 1:
                _logger.info("scheduled task running !")
            end_time = time.time()
        except Exception as e:
            # 记录异常信息
            _logger.error(f"scheduled task error: {str(e)}")
