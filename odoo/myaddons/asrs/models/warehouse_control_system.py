# -*- coding: utf-8 -*-
from odoo import models, fields, api

from .plc_connect import PlcClient

import logging
_logger = logging.getLogger(__name__)




class WarehouseControlSystem(models.Model):

     _name = 'warehouse.control.system'
     _description = 'warehouse control system'


     # life = fields.Boolean(string="心跳符号")
     # ready = fields.Boolean(string="准备就绪")
     factory = fields.Char(string="工厂代号")
     workshop = fields.Char(string="车间代号")
     line = fields.Char(string="线体代号")
     machine = fields.Char(string="机台代号")

     netcontrol = fields.Boolean(string='网络控制')
     netdata = fields.Boolean(string='网络数据')
     system_alarm = fields.Boolean(string='系统故障')
     system_ready = fields.Boolean(string='系统就绪')
     hardware_ready = fields.Boolean(string='硬件就绪')
     auto_ready = fields.Boolean(string='自动就绪')
     auto_take_finish = fields.Boolean(string='取料完成')
     auto_feed_finish = fields.Boolean(string='送料完成')
     auto_source_position = fields.Boolean(string='到源目标')
     auto_target_position = fields.Boolean(string='到新目标')
     auto_finish = fields.Boolean(string='任务完成')
     task_running = fields.Boolean(string='执行任务')
     none1 = fields.Boolean(string='无1')
     none2 = fields.Boolean(string='无2')
     estate = fields.Integer(string='状态')

     # 添加关联到输入输出信号的字段
     input_ids = fields.One2many('warehouse.control.system.input', 'wcs_id', string='输入信号')
     output_ids = fields.One2many('warehouse.control.system.output', 'wcs_id', string='输出信号')

     # 添加日志相关字段
     log_messages = fields.Text(string='Operation Logs', readonly=True)
     # first_40_logs = fields.Text(string='First 40 Logs', compute='_compute_first_40_logs', readonly=True)
     # last_40_logs = fields.Text(string='Last 40 Logs', compute='_compute_last_40_logs', readonly=True)
     first_30_logs = fields.Text(string='First 30 Logs', readonly=True)
     last_30_logs = fields.Text(string='Last 30 Logs', readonly=True)


     def control_system_read_write(self):
         self.automation_state_read()


     def automation_state_read(self):

        results = [
            {'db_number': 260, 'offset': 40, 'bit_index': 0, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 40, 'bit_index': 1, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 40, 'bit_index': 2, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 40, 'bit_index': 3, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 40, 'bit_index': 4, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 40, 'bit_index': 5, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 40, 'bit_index': 6, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 40, 'bit_index': 7, 'value_type': 'bool'},

            {'db_number': 260, 'offset': 41, 'bit_index': 0, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 41, 'bit_index': 1, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 41, 'bit_index': 2, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 41, 'bit_index': 3, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 41, 'bit_index': 4, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 41, 'bit_index': 5, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 44, 'value_type': 'int'},
        ]
        num = 0
        values_to_write = {}
        for result in results:
            num += 1
            # value = PlcClient().db_number_read(result)
            value = PlcClient().db_number_read(result)
            if num == 1:
                values_to_write['netcontrol'] = value
            elif num == 2:
                values_to_write['netdata'] = value
            elif num == 3:
                values_to_write['system_alarm'] = value
            elif num == 4:
                values_to_write['system_ready'] = value
            elif num == 5:
                values_to_write['hardware_ready'] = value
            elif num == 6:
                values_to_write['auto_ready'] = value
            elif num == 7:
                values_to_write['auto_take_finish'] = value
            elif num == 8:
                values_to_write['auto_feed_finish'] = value
            elif num == 9:
                values_to_write['auto_source_position'] = value
            elif num == 10:
                values_to_write['auto_target_position'] = value
            elif num == 11:
                values_to_write['auto_finish'] = value
            elif num == 12:
                values_to_write['task_running'] = value
            elif num == 13:
                values_to_write['none1'] = value
            elif num == 14:
                values_to_write['none2'] = value
            elif num == 15:
                values_to_write['estate'] = value
                # print(value)
        if values_to_write:
            record = self.browse(6)
            record.write(values_to_write)
            # print(values_to_write)

     def auto_start_scheduler(self):
         log_message = "scheduler task start follow system !"
         _logger.info(log_message)
         self.log_operation(log_message)
         print('auto start', log_message)
         self.env['warehouse.plc.task'].start_scheduler()


     def start_scheduler(self):
         self.env['warehouse.plc.task'].start_scheduler()
         log_message = "scheduler task start !"
         _logger.info(log_message)
         self.log_operation(log_message)

     def stop_scheduler(self):
         self.env['warehouse.plc.task'].stop_scheduler()
         log_message = "scheduler task stop !"
         _logger.info(log_message)
         self.log_operation(log_message)

     def log_operation(self, message):
         """记录操作日志，限制总记录数为100条以保持性能"""
         current_logs = self.log_messages or ""
         # 使用用户时区获取时间戳，解决时区不一致问题
         user_tz = self.env.user.tz or 'UTC'
         timestamp = fields.Datetime.context_timestamp(self.env.user, fields.Datetime.now()).strftime(
             "%Y-%m-%d %H:%M:%S")
         new_log = f"[{timestamp}] {message}\n"

         # 将现有日志按行分割
         log_lines = current_logs.splitlines()
         # 添加新日志到最前面
         log_lines.insert(0, f"[{timestamp}] {message}")
         # 只保留最新的100条记录以保持性能
         log_lines = log_lines[:100]
         # 重新组合日志
         self.log_messages = "\n".join(log_lines) + "\n"
         self.load_first_30_logs()
         self.load_last_30_logs()

     def load_first_30_logs(self):
         """计算并显示前35条日志记录"""
         for record in self:
             if record.log_messages:
                 log_lines = record.log_messages.splitlines()
                 # 获取前35条记录
                 first_lines = log_lines[:30]
                 # record.first_40_logs = "\n".join(first_lines)
                 # 为每行添加序号
                 numbered_lines = [f"{i + 1:2d}. {line}" for i, line in enumerate(first_lines)]
                 record.first_30_logs = "\n".join(numbered_lines)
             else:
                 record.first_30_logs = ""

     def load_last_30_logs(self):
         """计算并显示后35条日志记录"""
         for record in self:
             if record.log_messages:
                 log_lines = record.log_messages.splitlines()
                 # 只有当总记录数大于30条时才显示后30条记录
                 if len(log_lines) > 30:
                     if len(log_lines) > 60:
                         middle_lines = log_lines[30:60]
                         numbered_lines = [f"{i + 31:2d}. {line}" for i, line in enumerate(middle_lines)]
                         record.last_30_logs = "\n".join(numbered_lines)
                     else:
                         # 如果总记录数在31到60之间，显示从第31条到末尾的记录
                         middle_lines = log_lines[30:]
                         # record.last_40_logs = "\n".join(middle_lines)
                         # 为每行添加序号
                         numbered_lines = [f"{i + 31:2d}. {line}" for i, line in enumerate(middle_lines)]
                         record.last_30_logs = "\n".join(numbered_lines)
                 else:
                     # 如果总记录数不超过30条，则不显示任何内容
                     record.last_30_logs = ""
             else:
                 record.last_30_logs = ""





class WarehouseControlSystemInput(models.Model):
    _name = 'warehouse.control.system.input'
    _description = 'Warehouse Control System Input Signals'

    name = fields.Char(string="信号名称", required=True)
    address = fields.Char(string="地址", required=True)  # 如 I0.0, I0.1等
    value = fields.Boolean(string="状态")
    wcs_id = fields.Many2one('warehouse.control.system', string="控制系统", ondelete='cascade')

class WarehouseControlSystemOutput(models.Model):
    _name = 'warehouse.control.system.output'
    _description = 'Warehouse Control System Output Signals'

    name = fields.Char(string="信号名称", required=True)
    address = fields.Char(string="地址", required=True)  # 如 Q0.0, Q0.1等
    value = fields.Boolean(string="状态")
    wcs_id = fields.Many2one('warehouse.control.system', string="控制系统", ondelete='cascade')











































