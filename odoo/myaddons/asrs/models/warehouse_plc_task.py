# -*- coding: utf-8 -*-
import odoo
from odoo import models, fields, api
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import logging

_logger = logging.getLogger(__name__)


class WarehousePlcTask(models.Model):
    _name = 'warehouse.plc.task'
    _description = 'Warehouse Plc Taskr'

    name = fields.Char(string="调度器名称")
    active = fields.Boolean(default=True, string="启用")
    started = fields.Boolean(default=False, string="已启动")
    last_run = fields.Datetime(string="上次运行时间")
    heartbeat = fields.Boolean(string="PC心跳")
    ten_second = fields.Integer(string="每10秒")
    one_minute = fields.Integer(string="每分钟")

    # 使用类变量存储调度器实例
    _scheduler_instance = None
    # ten_second = 1
    # one_minute = 1
    @api.model
    def start_scheduler(self):
        """启动调度器"""
        # 将调度器实例作为类属性存储
        if not hasattr(self.__class__, '_scheduler_instance') or not self.__class__._scheduler_instance:
            self.__class__._scheduler_instance = BackgroundScheduler()

        # 查找或创建调度器记录
        scheduler_record = self.search([], limit=1)

        if not scheduler_record:
            scheduler_record = self.create({'name': 'PLC调度器'})

        # if not scheduler_record.started:
        if not self.__class__._scheduler_instance.running:

            # 添加每秒执行的任务
            self.__class__._scheduler_instance.add_job(self._execute_scheduled_tasks, 'interval', seconds=1,
                                                       max_instances=4)
            self.__class__._scheduler_instance.start()
            scheduler_record.write({'started': True})

            _logger.info("🚀 scheduler add job and start !")
            return True
        return False

    @api.model
    def stop_scheduler(self):
        """停止调度器"""
        # 检查是否存在调度器实例并且正在运行
        if hasattr(self.__class__, '_scheduler_instance') and self.__class__._scheduler_instance:
            if self.__class__._scheduler_instance.running:
                _logger.info("🛑 scheduled task stop !")
                # 停止调度器
                self.__class__._scheduler_instance.shutdown()
                # 更新记录状态
                scheduler_record = self.search([], limit=1)
                if scheduler_record:
                    scheduler_record.write({'started': False})
                return True
        return False

    def _execute_scheduled_tasks(self):
        """执行定时任务"""

        try:
            # 重新获取数据库连接和环境
            db_name = self.env.cr.dbname
            with odoo.sql_db.db_connect(db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})  # 使用管理员用户

        # try:
        #     # 使用 Odoo 的 registry 和 cursor 来安全地访问数据库
        #     with odoo.registry(self.env.cr.dbname).cursor() as cr:
        #         env = api.Environment(cr, 1, {})

                # # 更新执行时间
                scheduler = env['warehouse.plc.task'].search([], limit=1)
                # scheduler.write({'last_run': fields.Datetime.now()})
                heartbeat_value = not scheduler.heartbeat
                ten_second_value = (scheduler.ten_second + 1) % 9
                one_minute_value = (scheduler.one_minute + 1) % 59
                # print(heartbeat_value,ten_second_value,one_minute_value)
                scheduler.write({
                    'last_run': fields.Datetime.now(),
                    'heartbeat' : heartbeat_value,
                    'ten_second': ten_second_value,
                    'one_minute': one_minute_value
                })

                env['warehouse.control.system'].control_system_read_write()
                if ten_second_value == 0:
                    env['warehouse.system.operate'].system_operate_read_write()

                if one_minute_value == 0:
                    _logger.info("scheduler task running !")

                # self.__class__.ten_second = (self.__class__.ten_second + 1) % 10
                # self.__class__.one_minute = (self.__class__.one_minute + 1) % 60
                # print(self.__class__.ten_second, self.__class__.one_minute)

        except Exception as e:
            _logger.error(f"❌ scheduled task error: {str(e)}")

















































