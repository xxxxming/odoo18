# -*- coding: utf-8 -*-
import odoo
from odoo import models, fields, api
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import logging
import time

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
    few_minutes = fields.Integer(string="几分钟")
    instance_id = fields.Integer(string="实例编号")  # 新增字段，用于区分不同实例

    # 类变量存调度器实例
    _scheduler_instance = None


    @api.model
    def start_scheduler(self):
        """启动调度器"""
        if not hasattr(self.__class__, '_scheduler_instance') or not self.__class__._scheduler_instance:
            self.__class__._scheduler_instance = BackgroundScheduler()

        # 确保每个实例对应一条记录
        for instance_id in range(1, 5):  # 4 个实例
            record = self.search([('instance_id', '=', instance_id)], limit=1)
            if not record:
                self.create({
                    'name': f'PLC调度器-实例{instance_id}',
                    'instance_id': instance_id
                })

        if not self.__class__._scheduler_instance.running:
            _logger.info("🚀 scheduled task start !")
            for instance_id in range(1, 5):
                self.__class__._scheduler_instance.add_job(
                    self._execute_scheduled_tasks,
                    'interval',
                    seconds=1,
                    max_instances=1,  # 每个实例内部单线程
                    coalesce=True,
                    kwargs={'instance_id': instance_id}
                )
            self.__class__._scheduler_instance.start()
            self.search([]).write({'started': True})
            return True
        return False

    @api.model
    def stop_scheduler(self):
        """停止调度器"""
        if hasattr(self.__class__, '_scheduler_instance') and self.__class__._scheduler_instance:
            if self.__class__._scheduler_instance.running:
                _logger.info("🛑 scheduled task stop !")
                self.__class__._scheduler_instance.shutdown()
                self.search([]).write({'started': False})
                return True
        return False

    def _execute_scheduled_tasks(self, instance_id):
        """执行定时任务（区分实例）"""
        try:
            db_name = self.env.cr.dbname
            with odoo.sql_db.db_connect(db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})  # 管理员环境

                scheduler = env['warehouse.plc.task'].search(
                    [('instance_id', '=', instance_id)], limit=1)

                now = fields.Datetime.now()
                current_second = now.second

                # new_ten_second = scheduler.ten_second + 1
                # new_few_minutes = scheduler.few_minutes + 1
                # # print(new_ten_second)
                # if new_ten_second > 9:
                #     new_ten_second = 1
                # if new_few_minutes > 59:
                #     new_few_minutes = 1
                #
                # # 将更新写入数据库
                # scheduler.write({'ten_second': new_ten_second,
                #                  'few_minutes': new_few_minutes,
                #                  'last_run': fields.Datetime.now()
                #                  })

                if scheduler.instance_id == 1:
                    time.sleep(0.43)
                    # print("Task sleep 0.2")
                    env['warehouse.control.system'].control_system_read_write()

                if scheduler.instance_id == 2:
                    # time.sleep(0.63)
                    # print("Task sleep 0.4")
                    env['warehouse.system.operate'].system_operate_read_write()


                if current_second == 1:
                    _logger.info(f"✅ scheduled task running，scheduler {instance_id} ！")

        except Exception as e:
            _logger.error(f"❌ scheduled task error，scheduler {instance_id}: {str(e)}")












































