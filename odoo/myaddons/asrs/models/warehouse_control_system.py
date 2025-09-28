# -*- coding: utf-8 -*-
from odoo import models, fields, api

from .plc_connect import PlcClient

from odoo.addons.bus.models.bus import channel_with_db

import time
import logging
_logger = logging.getLogger(__name__)

old_channel_control = 0


class WarehouseControlSystem(models.Model):

     _name = 'warehouse.control.system'
     _description = 'warehouse control system'


     life_signal = fields.Boolean(string='生命信号')
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
     entrance1_goods = fields.Boolean(string='入口1货物')
     entrance2_goods = fields.Boolean(string='入口2货物')
     none3 = fields.Boolean(string='无3')
     none4 = fields.Boolean(string='无4')

     online_control = fields.Integer(string='控制信号')
     online_download = fields.Integer(string='在线下载')
     online_update = fields.Integer(string='数据更新')
     online_upload = fields.Integer(string='在线上传')
     estate = fields.Integer(string='状态')

     # 添加关联到输入输出信号的字段
     # input_ids = fields.One2many('warehouse.control.system.input', 'wcs_id', string='输入信号')
     # output_ids = fields.One2many('warehouse.control.system.output', 'wcs_id', string='输出信号')

     # 添加日志相关字段
     log_messages = fields.Text(string='Operation Logs', readonly=True)
     # first_40_logs = fields.Text(string='First 40 Logs', compute='_compute_first_40_logs', readonly=True)
     # last_40_logs = fields.Text(string='Last 40 Logs', compute='_compute_last_40_logs', readonly=True)
     first_30_logs = fields.Text(string='First 30 Logs', readonly=True)
     last_30_logs = fields.Text(string='Last 30 Logs', readonly=True)



     def control_system_read_write(self):
         # self.channel_control_read_write()
         self.online_read_write()
         record = self.browse(1)
         online_update = record.online_update
         online_upload = record.online_upload
         online_download = record.online_download

         # # PLC状态有该改变时更新
         # online_update_bit = {}
         # for i in range(8):  # 检查前8位
         #     online_update_bit[f'bit_{i}'] = bool((online_update >> i) & 1)
         # if online_update_bit['bit_0']:
         #     self.automation_state_read(262)
         #     self.channel_control_bit(0, True)
         # else:
         #     self.channel_control_bit(0, False)

         # 计算机心跳信号
         online_upload_bit = {}
         for i in range(8):  # 检查前8位
             online_upload_bit[f'bit_{i}'] = bool((online_upload >> i) & 1)
         # if online_upload_bit['bit_0']:
         #     # self.online_download_bit(0, True)
         #     new_value = online_download | (1 << 0)
         # else:
         #     # self.online_download_bit(0, False)
         #     new_value = online_download & ~(1 << 0)
         #
         # if online_upload_bit['bit_1']:
         #     self.automation_state_read(262)
         #     print('reading states')
         #     # self.online_download_bit(1, True)
         #     new_value = online_download | (1 << 1)
         # else:
         #     # self.online_download_bit(1, False)
         #     new_value = online_download & ~(1 << 1)

         # 构建新的online_download值
         new_online_download = online_download

         # 处理bit_0
         if online_upload_bit['bit_0']:
             new_online_download = new_online_download | (1 << 0)  # 设置bit_0为1
         else:
             new_online_download = new_online_download & ~(1 << 0)  # 设置bit_0为0

         # 处理bit_1
         if online_upload_bit['bit_1']:
             self.automation_state_read(262)
             new_online_download = new_online_download | (1 << 1)  # 设置bit_1为1
         else:
             new_online_download = new_online_download & ~(1 << 1)  # 设置bit_1为0

         # 只有在值发生变化时才写入数据库
         if online_download != new_online_download:
             # record.write({'online_download': new_online_download})
             # _logger.info(f"online_download updated, value {online_download} changed to {new_online_download}")

             max_retries = 10
             retry_count = 0
             while retry_count < max_retries:
                 try:
                     record.write({'online_download': new_online_download})
                     if retry_count > 0:
                         _logger.info(f"Successfully updated warehouse control system after {retry_count} retries")
                     break
                 except Exception as e:
                     if "由于同步更新而无法串行访问" in str(e) or "could not serialize access" in str(e):
                         retry_count += 1
                         if retry_count >= max_retries:
                             _logger.error(
                                 f"Failed to update warehouse control system after {max_retries} retries: {str(e)}")
                             raise
                         else:
                             # 增加等待时间以减少冲突概率
                             wait_time = 0.1 * retry_count + 0.1 * (hash(str(record.id) + str(retry_count)) % 10) / 10
                             _logger.warning(
                                 f"Retrying update warehouse control system due to serialization conflict, attempt {retry_count}, waiting {wait_time:.2f}s")
                             time.sleep(wait_time)
                     else:
                         raise

     # @api.model
     # def channel_control_bit(self, bit_position, bit_value):
     #     """更新channel_control的指定位"""
     #     record = self.browse(6)
     #     current_value = record.online_control
     #
     #     if bit_value:
     #         # 设置位为1
     #         new_value = current_value | (1 << bit_position)
     #     else:
     #         # 设置位为0
     #         new_value = current_value & ~(1 << bit_position)
     #
     #     # 只有在值发生变化时才写入数据库
     #     if current_value != new_value:
     #         print('control bit',new_value)
     #         time.sleep(0.3)
     #         record.write({'online_control': new_value})
     #         _logger.info(f"online_control bit{bit_position} updated to {bit_value}，value {current_value} changed to {new_value}")

     # @api.model
     # def online_download_bit(self, bit_position, bit_value):
     #     """更新channel_control的指定位"""
     #     record = self.browse(6)
     #     current_value = record.online_download
     #
     #     if bit_value:
     #         # 设置位为1
     #         new_value = current_value | (1 << bit_position)
     #     else:
     #         # 设置位为0
     #         new_value = current_value & ~(1 << bit_position)
     #
     #     # 只有在值发生变化时才写入数据库
     #     if current_value != new_value:
     #         record.write({'online_download': new_value})


     def automation_state_read(self,address):

        results = [
            {'db_number': 260, 'offset': address, 'bit_index': 0, 'value_type': 'bool'},
            {'db_number': 260, 'offset': address, 'bit_index': 1, 'value_type': 'bool'},
            {'db_number': 260, 'offset': address, 'bit_index': 2, 'value_type': 'bool'},
            {'db_number': 260, 'offset': address, 'bit_index': 3, 'value_type': 'bool'},
            {'db_number': 260, 'offset': address, 'bit_index': 4, 'value_type': 'bool'},
            {'db_number': 260, 'offset': address, 'bit_index': 5, 'value_type': 'bool'},
            {'db_number': 260, 'offset': address, 'bit_index': 6, 'value_type': 'bool'},
            {'db_number': 260, 'offset': address, 'bit_index': 7, 'value_type': 'bool'},

            {'db_number': 260, 'offset': address+1, 'bit_index': 0, 'value_type': 'bool'},
            {'db_number': 260, 'offset': address+1, 'bit_index': 1, 'value_type': 'bool'},
            {'db_number': 260, 'offset': address+1, 'bit_index': 2, 'value_type': 'bool'},
            {'db_number': 260, 'offset': address+1, 'bit_index': 3, 'value_type': 'bool'},
            {'db_number': 260, 'offset': address+1, 'bit_index': 4, 'value_type': 'bool'},
            {'db_number': 260, 'offset': address+1, 'bit_index': 5, 'value_type': 'bool'},
            {'db_number': 260, 'offset': address+1, 'bit_index': 6, 'value_type': 'bool'},
            {'db_number': 260, 'offset': address+1, 'bit_index': 7, 'value_type': 'bool'},

            {'db_number': 260, 'offset': address+4, 'value_type': 'int'},

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
                values_to_write['entrance1_goods'] = value
            elif num == 14:
                values_to_write['entrance2_goods'] = value
            elif num == 15:
                values_to_write['none3'] = value
            elif num == 16:
                values_to_write['none4'] = value

            elif num == 17:
                values_to_write['estate'] = value
                print('read estate',value)
        if values_to_write:
            record = self.browse(1)
            # 检查哪些字段发生了变化
            changed_fields = {}
            for field, new_value in values_to_write.items():
                old_value = getattr(record,field)
                if old_value != new_value:
                    changed_fields[field] = new_value
                    _logger.info(f"field {field} changed，old value：{old_value}，new value：{new_value}")
            print('estate change',changed_fields)
            # 只有当有字段发生变化时才更新并发送通知
            if changed_fields:
                record.write(changed_fields)
                # 发送通知到前端，只包含变化的字段
                self.env['bus.bus']._sendone(
                    channel_with_db(self.env.cr.dbname, 'warehouse_control_update'),
                    'warehouse.control_update',
                    {
                        'model': 'warehouse.control.system',
                        'id': record.id,
                        'changed_fields': changed_fields
                    }
                )

     def online_read_write(self):

         record = self.browse(1)
         online_control = record.online_control
         online_download = record.online_download

         data_list = [
             {'value': online_control, "db_number": 260, 'offset': 282, 'value_type': 'dint'},
             {'value': online_download, "db_number": 260, 'offset': 286, 'value_type': 'dint'},
         ]
         for data in data_list:
             PlcClient().db_number_write(data)


         results = [
             {'db_number': 260, 'offset': 290, 'value_type': 'dint'},
             {'db_number': 260, 'offset': 294, 'value_type': 'dint'},
         ]
         num = 0
         values_to_write = {}
         for result in results:
             num += 1
             value = PlcClient().db_number_read(result)
             if num == 1:
                 values_to_write['online_update'] = value
             if num == 2:
                 values_to_write['online_upload'] = value

         # 只有当值发生变化时才写入数据库
         if values_to_write:
             # 检查哪些字段发生了变化
             changed_fields = {}
             for field, new_value in values_to_write.items():
                 old_value = getattr(record, field)
                 if old_value != new_value:
                     changed_fields[field] = new_value
                     # _logger.info(f"field {field} changed，old value：{old_value}，new value：{new_value}")
             # 只有当有字段发生变化时才写入数据库
             # if changed_fields:
             #     record.write(changed_fields)

             if changed_fields:
                 # 添加重试机制处理并发冲突
                 max_retries = 5
                 retry_count = 0
                 while retry_count < max_retries:
                     try:
                         record.write(changed_fields)
                         break
                     except Exception as e:
                         if "由于同步更新而无法串行访问" in str(e) or "could not serialize access" in str(e):
                             retry_count += 1
                             if retry_count >= max_retries:
                                 _logger.warning(f"Failed to update warehouse control system after {max_retries} retries: {str(e)}")
                                 raise
                             else:
                                 # 等待随机时间后重试
                                 time.sleep(0.1 * retry_count + 0.1 * (hash(str(record.id)) % 10) / 10)
                                 _logger.warning(f"Retrying update warehouse control system due to serialization conflict, attempt {retry_count}")
                         else:
                             raise


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

# class WarehouseControlSystemInput(models.Model):
#     _name = 'warehouse.control.system.input'
#     _description = 'Warehouse Control System Input Signals'
#
#     name = fields.Char(string="信号名称", required=True)
#     address = fields.Char(string="地址", required=True)  # 如 I0.0, I0.1等
#     value = fields.Boolean(string="状态")
#     wcs_id = fields.Many2one('warehouse.control.system', string="控制系统", ondelete='cascade')
#
# class WarehouseControlSystemOutput(models.Model):
#     _name = 'warehouse.control.system.output'
#     _description = 'Warehouse Control System Output Signals'
#
#     name = fields.Char(string="信号名称", required=True)
#     address = fields.Char(string="地址", required=True)  # 如 Q0.0, Q0.1等
#     value = fields.Boolean(string="状态")
#     wcs_id = fields.Many2one('warehouse.control.system', string="控制系统", ondelete='cascade')
#










































