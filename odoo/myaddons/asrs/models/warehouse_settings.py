# -*- coding: utf-8 -*-
from odoo import models, fields, api
from .warehouse_system_operate import WarehouseSystemOperate
from .plc_connect import PlcClient
import logging
_logger = logging.getLogger(__name__)
logging.getLogger('apscheduler').setLevel(logging.WARNING)
from odoo.exceptions import UserError


class WarehouseSettings(models.Model):

     _name = 'warehouse.settings'
     _description = 'Warehouse settings'

     warehouse_name = fields.Char(string='仓库名称')
     building = fields.Integer(string='栋数')
     stacker_quantity = fields.Integer(string='堆垛机数')
     column = fields.Integer(string='列数')
     layer = fields.Integer(string='层数')
     entrance_1 = fields.Char(string='出入口1')
     entrance_2 = fields.Char(string='出入口2')
     entrance_3 = fields.Char(string='出入口3')
     entrance_4 = fields.Char(string='出入口4')
     layer_spacing = fields.Float(string='层间距')
     column_spacing = fields.Float(string='列间距')
     total_locations = fields.Integer(string='库位总数',compute='_compute_total_locations',store=True)


     sync_location = fields.Integer(string='同步库位')
     sync_building = fields.Integer(string='同步栋')
     sync_column = fields.Integer(string='同步列')
     sync_layer = fields.Integer(string='同步层')

     sync_total_locations = fields.Integer(string='同步总库位',)
     synchronized_already = fields.Integer(string='已同步数')

     # 添加库位同步日志相关字段
     sync_location_logs = fields.Text(string='Operation Logs', readonly=True)
     first_30_location_logs = fields.Text(string='First 30 Logs', readonly=True)
     last_30_location_logs = fields.Text(string='Last 30 Logs', readonly=True)
     # 添加库位同步日志相关字段
     sync_pack_code_logs = fields.Text(string='Operation Logs', readonly=True)
     first_30_pack_code_logs = fields.Text(string='First 30 Logs', readonly=True)
     last_30_pack_code_logs = fields.Text(string='Last 30 Logs', readonly=True)

     @api.depends('building','column','layer')
     def _compute_total_locations(self):
          for record in self:
               record.total_locations = record.building * record.column * record.layer


     @api.onchange('sync_location')
     def _onchange_sync_location(self):

          record = self.env['warehouse.location.information']
          self.sync_building,self.sync_column,self.sync_layer=record.location_disintegrate(self.sync_location)
          self.sync_location_write(82)

     def sync_location_write(self, db_address):
          """传递到PLC进行写入"""

          sync_building = self.sync_building
          sync_column = self.sync_column
          sync_layer = self.sync_layer
          sync_location = self.sync_location

          try:
               # 批量写入
               data_list = [
                    {'value': sync_building, "db_number": 260, 'offset': db_address + 0, 'value_type': 'int'},
                    {'value': sync_column, "db_number": 260, 'offset': db_address + 2, 'value_type': 'int'},
                    {'value': sync_layer, "db_number": 260, 'offset': db_address + 4, 'value_type': 'int'},
                    {'value': sync_location, "db_number": 260, 'offset': db_address + 6, 'value_type': 'dint'},

               ]
               for data in data_list:
                    PlcClient().db_number_write(data)
          except Exception as e:
               _logger.error(f"库位信息写入失败！: {str(e)}")
               raise

          pass

     def sync_information_write(self,location,db_address):
          """传递到PLC进行写入"""

          info_record = self.env['warehouse.location.information'].search(
               [('location_number', '=', location)], limit=1)

          if info_record:
               goods_status = info_record.goods_status
               base_number = info_record.base_number
               pack_number = info_record.pack_number
               location_number = info_record.location_number
               pack_barcode = info_record.pack_barcode

          try:
               # 批量写入
               data_list = [
                    {'value': goods_status, "db_number": 262, 'offset': db_address+0, 'bit_index': 0,'value_type': 'bool'},
                    {'value': base_number, "db_number": 262, 'offset': db_address+2, 'value_type': 'int'},
                    {'value': pack_number, "db_number": 262, 'offset': db_address+4, 'value_type': 'int'},
                    {'value': location_number, "db_number": 262, 'offset': db_address+6, 'value_type': 'dint'},
                    {'value': pack_barcode, "db_number": 262, 'offset': db_address+10, "string_max_len": 18,'value_type': 'string'}
               ]
               for data in data_list:
                    PlcClient().db_number_write(data)
          except Exception as e:
               _logger.error(f"库位信息写入失败！: {str(e)}")
               raise

     def sync_information_read(self, location,db_address):
          """读取测试-批量"""
          results = [
               # 库位有货，序号，框号，库位号，框条码
               {'db_number': 262, 'offset': db_address+0, 'value_type': 'bool', 'bit_index': 0},
               {'db_number': 262, 'offset': db_address+2, 'value_type': 'int'},
               {'db_number': 262, 'offset': db_address+4, 'value_type': 'int'},
               {'db_number': 262, 'offset': db_address+6, 'value_type': 'dint'},
               {'db_number': 262, 'offset': db_address+10, 'value_type': 'string', "string_max_len": 18},
          ]
          num = 0
          values_to_write = {}
          for result in results:
               num += 1
               value = PlcClient().db_number_read(result)
               if num == 1:
                    values_to_write['goods_status'] = value
               # elif num == 2:
               #      values_to_write['base_number'] = value
               elif num == 3:
                    values_to_write['pack_number'] = value
               elif num == 4:
                    values_to_write['location_number'] = value
                    read_location_number = value
               elif num == 5:
                    values_to_write['pack_barcode'] = value
          if values_to_write:
               # record = self.browse(1)
               # record = self.env['warehouse.system.operate'].browse(1)
               info_record = self.env['warehouse.location.information'].search(
                    [('location_number', '=', location)], limit=1)
               if info_record:
                    if location == read_location_number :
                       info_record.write(values_to_write)
                    else :
                        raise UserError(f"读取到库位编号{read_location_number}与同步库位编号{location}不一致 !")
               else :
                    raise UserError(f"没查找到库位编号 {location} 数据 !")
               print(values_to_write)

     def sync_locations_read(self):
          self.sync_information_read(self.sync_location, 160)

          log_message = f"读取库位：{self.sync_location} 同步完成 ！"
          _logger.info(log_message)
          self.log_sync_location(log_message)

     def sync_locations_write(self):
         self.sync_information_write(self.sync_location,192)

         log_message = f"写入库位：{self.sync_location} 同步完成 ！"
         _logger.info(log_message)
         self.log_sync_location(log_message)

     def sync_building_read(self):

         pass

     def sync_building_write(self):

         pass

     def sync_column_read(self):
          # 获取设定数据
          warehouse_settings = self.env['warehouse.settings'].search([], limit=1)
          setting_building = warehouse_settings.building
          setting_column = warehouse_settings.column
          setting_layer = warehouse_settings.layer

          building = self.sync_building
          column = self.sync_column
          layer = 0
          start_address = 224-32
          # 同步列数据，读取同一列的每一层数据进行同步
          for i in range(0, setting_column):
               layer += 1
               location = building*10000 + column*100 + layer
               start_address += 32
               try:
                    self.sync_information_read(location, start_address)
               except Exception as e:
                    _logger.error(f"同步库位 {location} 失败: {str(e)}")
                    # 记录错误但继续处理其他库位
                    continue
               print(layer,location)
          pass

     def sync_column_write(self):
          # 获取设定数据
          warehouse_settings = self.env['warehouse.settings'].search([], limit=1)
          setting_building = warehouse_settings.building
          setting_column = warehouse_settings.column
          setting_layer = warehouse_settings.layer

          building = self.sync_building
          column = self.sync_column
          layer = 0
          start_address = 864-32

          # 同步列数据，写入同一列的每一层数据进行同步
          for i in range(0,setting_layer):
               layer += 1
               location = building*10000 + column*100 + layer
               start_address += 32
               try:
                    self.sync_information_write(location, start_address)
               except Exception as e:
                    _logger.error(f"同步库位 {location} 失败: {str(e)}")
                    # 记录错误但继续处理其他库位
                    continue
               print(layer,location)


     def sync_layer_read(self):
          # 获取设定数据
          warehouse_settings = self.env['warehouse.settings'].search([], limit=1)
          setting_building = warehouse_settings.building
          setting_column = warehouse_settings.column
          setting_layer = warehouse_settings.layer

          building = self.sync_building
          column = 0
          layer = self.sync_layer
          start_address = 1504-32
          # 同步层数据，读取不同列的同一层数据进行同步
          for i in range(1, setting_column + 1):
               column += 1
               location = building * 10000 + column * 100 + layer
               start_address += 32
               try:
                    self.sync_information_read(location, start_address)
               except Exception as e:
                    _logger.error(f"同步库位 {location} 失败: {str(e)}")
                    # 记录错误但继续处理其他库位
                    continue

               print(column, location)
          pass

     def sync_layer_write(self):
          # 获取设定数据
          warehouse_settings = self.env['warehouse.settings'].search([], limit=1)
          setting_building = warehouse_settings.building
          setting_column = warehouse_settings.column
          setting_layer = warehouse_settings.layer

          building = self.sync_building
          column = 0
          layer = self.sync_layer
          start_address = 2144-32
          # 同步层数据，写入不同列的同一层数据进行同步
          for i in range(0, setting_column):
               column += 1
               location = building * 10000 + column * 100 + layer
               start_address += 32
               try:
                    self.sync_information_write(location, start_address)
               except Exception as e:
                    _logger.error(f"同步库位 {location} 失败: {str(e)}")
                    # 记录错误但继续处理其他库位
                    continue
               print(layer,location)




     # Logs
     def log_sync_location(self, message):
          """记录操作日志，限制总记录数为100条以保持性能"""
          current_logs = self.sync_location_logs or ""
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
          self.sync_location_logs = "\n".join(log_lines) + "\n"
          self.load_first_30_location_logs()
          self.load_last_30_location_logs()

     def load_first_30_location_logs(self):
          """计算并显示前35条日志记录"""
          for record in self:
               if record.sync_location_logs:
                    log_lines = record.sync_location_logs.splitlines()
                    # 获取前35条记录
                    first_lines = log_lines[:30]
                    # record.first_40_logs = "\n".join(first_lines)
                    # 为每行添加序号
                    numbered_lines = [f"{i + 1:2d}. {line}" for i, line in enumerate(first_lines)]
                    record.first_30_location_logs = "\n".join(numbered_lines)
               else:
                    record.first_30_location_logs = ""

     def load_last_30_location_logs(self):
          """计算并显示后35条日志记录"""
          for record in self:
               if record.sync_location_logs:
                    log_lines = record.sync_location_logs.splitlines()
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
                              record.last_30_location_logs = "\n".join(numbered_lines)
                    else:
                         # 如果总记录数不超过30条，则不显示任何内容
                         record.last_30_location_logs = ""
               else:
                    record.last_30_location_logs = ""

     def log_sync_pack_code(self, message):
          """记录操作日志，限制总记录数为100条以保持性能"""
          current_logs = self.sync_pack_code_logs or ""
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
          self.sync_location_logs = "\n".join(log_lines) + "\n"
          self.load_first_30_pack_code_logs()
          self.load_last_30_pack_code_logs()

     def load_first_30_pack_code_logs(self):
          """计算并显示前35条日志记录"""
          for record in self:
               if record.sync_pack_code_logs:
                    log_lines = record.sync_pack_code_logs.splitlines()
                    # 获取前35条记录
                    first_lines = log_lines[:30]
                    # record.first_40_logs = "\n".join(first_lines)
                    # 为每行添加序号
                    numbered_lines = [f"{i + 1:2d}. {line}" for i, line in enumerate(first_lines)]
                    record.first_30_pack_code_logs = "\n".join(numbered_lines)
               else:
                    record.first_30_pack_code_logs = ""

     def load_last_30_pack_code_logs(self):
          """计算并显示后35条日志记录"""
          for record in self:
               if record.sync_pack_code_logs:
                    log_lines = record.sync_pack_code_logs.splitlines()
                    # 只有当总记录数大于30条时才显示后30条记录
                    if len(log_lines) > 30:
                         if len(log_lines) > 60:
                              middle_lines = log_lines[30:60]
                              numbered_lines = [f"{i + 31:2d}. {line}" for i, line in enumerate(middle_lines)]
                              record.last_30_pack_code_logs = "\n".join(numbered_lines)
                         else:
                              # 如果总记录数在31到60之间，显示从第31条到末尾的记录
                              middle_lines = log_lines[30:]
                              # record.last_40_logs = "\n".join(middle_lines)
                              # 为每行添加序号
                              numbered_lines = [f"{i + 31:2d}. {line}" for i, line in enumerate(middle_lines)]
                              record.last_30_pack_code_logs = "\n".join(numbered_lines)
                    else:
                         # 如果总记录数不超过30条，则不显示任何内容
                         record.last_30_pack_code_logs = ""
               else:
                    record.last_30_pack_code_logs = ""