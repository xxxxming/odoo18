# -*- coding: utf-8 -*-
import odoo
from odoo import models, fields, api
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import logging
from .warehouse_scheduler import PlcScheduler
_logger = logging.getLogger(__name__)


# # ... existing code ...
#
# class WarehousePlcTask(models.Model):
#     _description = 'warehouse plc task'
#     _name = 'warehouse.plc.task'
#     # _inherit = ['mail.thread', 'mail.activity.mixin']
#     name = fields.Char(string="任务名称")
#     task_id = fields.Many2one('warehouse.plc.task', string="任务")
#     task_type = fields.Selection([('auto', '自动任务'), ('manual', '手动任务')], string="任务类型")
#     task_state = fields.Selection([('waiting', '等待中'), ('running', '运行中'), ('done', '完成'), ('cancel', '取消')],
#                                   string="任务状态")
#     task_time = fields.Datetime(string="任务时间")
#     task_result = fields.Text(string="任务结果")
#
#     def _start_scheduler_once(self):
#         plc_scheduler = PlcScheduler(self.env)
#         if not plc_scheduler.started:
#             def _thread():
#                 plc_scheduler.start()
#
#             t = threading.Thread(target=_thread)
#             t.setDaemon(True)
#             t.start()
#             print('test thread!')


class WarehousePlcTask(models.Model):
    _name = 'warehouse.plc.task'
    _description = 'Warehouse Plc Taskr'

    name = fields.Char(string="调度器名称")
    active = fields.Boolean(default=True, string="启用")
    started = fields.Boolean(default=False, string="已启动")
    last_run = fields.Datetime(string="上次运行时间")

    # 使用类变量存储调度器实例
    _scheduler_instance = None

    @api.model
    def start_scheduler(self):
        """启动调度器"""
        print('start_scheduler')
        # 将调度器实例作为类属性存储
        if not hasattr(self.__class__, '_scheduler_instance') or not self.__class__._scheduler_instance:
            self.__class__._scheduler_instance = BackgroundScheduler()

        # 查找或创建调度器记录
        scheduler_record = self.search([], limit=1)

        if not scheduler_record:
            scheduler_record = self.create({'name': 'PLC调度器'})
        print(scheduler_record,scheduler_record.started)
        if not scheduler_record.started:
            _logger.info("🚀 启动 ORM PLC 调度器")
            # 添加每秒执行的任务
            self.__class__._scheduler_instance.add_job(self._execute_scheduled_tasks, 'interval', seconds=1,
                                                       max_instances=4)
            self.__class__._scheduler_instance.start()
            scheduler_record.write({'started': True})
            return True
        return False



    def _execute_scheduled_tasks(self):
        """执行定时任务"""
        # try:
        #     # 更新执行时间
        #     self.search([], limit=1).write({'last_run': fields.Datetime.now()})
        #
        #     # 在这里执行实际的PLC任务
        #     # 示例：调用系统操作模型的方法
        #     # self.env['warehouse.system.operate'].control_system_read_write()
        #
        #     _logger.info("✅ ORM PLC 每秒任务执行完成")
        #
        # except Exception as e:
        #     _logger.error(f"❌ ORM PLC 每秒任务执行错误: {str(e)}")

        """执行定时任务"""
        try:
            # 重新获取数据库连接和环境
            db_name = self.env.cr.dbname
            with odoo.sql_db.db_connect(db_name).cursor() as cr:
                env = api.Environment(cr, 1, {})  # 使用管理员用户

                # 更新执行时间
                scheduler = env['warehouse.plc.task'].search([], limit=1)
                scheduler.write({'last_run': fields.Datetime.now()})

                # 在这里执行实际的PLC任务
                # 示例：调用系统操作模型的方法
                env['warehouse.system.operate'].system_operate_read_write()

                env['warehouse.control.system'].control_system_read_write()

                _logger.info("✅ ORM PLC 每秒任务执行完成")

        except Exception as e:
            _logger.error(f"❌ ORM PLC 每秒任务执行错误: {str(e)}")

















































