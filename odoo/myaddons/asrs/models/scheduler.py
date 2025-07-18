import os
import sys

from apscheduler.schedulers.background import BackgroundScheduler
import logging
from odoo import models, fields
from .control_system_operate import ControlSystemOperate
from .warehouse_communication import New_Public_PlcInterfaces
from .control_system_operate import ControlSystemOperate
import odoo
from odoo import api
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)

class PlcScheduler():
    def __init__(self):
        self.env = None
        self.scheduler = BackgroundScheduler()
        self.started = False
        self.one_second = 0
        self.ten_second = 0

    def start(self):
        """
        启动调度器，初始化定时任务。
        如果调度器未启动，则添加每100秒执行一次的one_second_task任务，
        并启动调度器。
        """
        if not self.started:
            _logger.info("🚀 启动 PLC 调度器")
            #添加间隔任务：每1秒调用一次 one_second_task 方法
            self.scheduler.add_job(self.one_second_task, 'interval', seconds=2, max_instances=4)
            # 添加间隔任务：每10秒调用一次 one_second_task 方法
            self.scheduler.add_job(self.ten_second_task, 'interval', seconds=20, max_instances=4)
            # 启动后台调度器
            self.scheduler.start()
            self.started = True

    def one_second_task(self):
        """00
        每秒执行的任务，调用 New_Public_PlcInterfaces 的 one_second_0task 方法。0
        用于处理与 PLC（可编程逻辑控制器）的通信任务。
        """
        db_name = 'odoo18e'  # ← 修改为你自己的数据库名
        with odoo.sql_db.db_connect(db_name).cursor() as cr:
            env = api.Environment(cr, 1, {})  # 1 表示超级管理员 user_id
        try:
            # 调用 New_Public_PlcInterfaces 类的 one_second_task 方法
            result = New_Public_PlcInterfaces(env)
            result.one_second_task()

            self.one_second = (self.one_second + 1) % 60
            if self.one_second == 1:
             _logger.info("one second task running")

        except Exception as e:
            # 记录异常信息
            _logger.error(f"PLC 每秒任务发生错误: {str(e)}")

    def ten_second_task(self):
        """
        每秒执行的任务，调用 New_Public_PlcInterfaces 的 one_second_task 方法。
        用于处理与 PLC（可编程逻辑控制器）的通信任务。
        """
        db_name = 'odoo18e'  # ← 修改为你自己的数据库名
        with odoo.sql_db.db_connect(db_name).cursor() as cr:
            env = api.Environment(cr, 1, {})  # 1 表示超级管理员 user_id
        try:
            result = New_Public_PlcInterfaces(env)
            result.ten_second_task()

            self.ten_second = (self.ten_second + 1) % 60
            if self.ten_second == 1:
                _logger.info("ten second task running")

        except Exception as e:
            # 记录异常信息
            _logger.error(f"PLC 每10秒任务发生错误: {str(e)}")
