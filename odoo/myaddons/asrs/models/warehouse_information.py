# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError

class WarehouseLocationInformation(models.Model):
     _name = 'warehouse.location.information'
     _description = 'warehouse location information'

     goods_status = fields.Boolean(string='库位有货')
     goods_cancel = fields.Boolean(string='取消库位')
     fixed_pack_number = fields.Boolean(string='绑定框号')
     fixed_pack_barcode = fields.Boolean(string='绑定条码')
     pack_number = fields.Integer(string='框号')
     base_number = fields.Integer(string='序号',readonly=True)
     location_number = fields.Integer(string='库位号',readonly=True)
     pack_barcode = fields.Char(string='框条码')

     def location_integrate(self,building,column,layer):
          # 获取 warehouse.settings 配置
          settings = self.env['warehouse.settings'].search([], limit=1)
          if not settings:
               _logger.error("未找到参数，请先设置基本参数!")
               raise UserError("未找到参数，请先设置基本参数!")
          if building > settings.building:
               _logger.error(f"栋参数 {building} 超出最大允许值 {settings.building} !")
               raise UserError(f"栋参数 {building} 超出最大允许值 {settings.building} !")
          if column > settings.column:
               _logger.error(f"Column {column} 超出最大允许值 {settings.column} ！")
               raise UserError(f"Column {column} 超出最大允许值 {settings.column} ！")
          if layer > settings.layer:
               _logger.error(f"Layer {layer} 超出最大允许值 {settings.layer} !")
               raise UserError(f"Layer {layer} 超出最大允许值 {settings.layer} !")

          # 组合数值：每两位表示一个字段 (building -> 前两位, column -> 中间两位, layer -> 最后两位)
          location = building * 10000 + column * 100 + layer
          return location

     def location_disintegrate(self,location):
          # 获取 warehouse.settings 配置
          settings = self.env['warehouse.settings'].search([], limit=1)
          if not settings:
               _logger.error("未找到参数，请先设置基本参数!")
               raise UserError("未找到参数，请先设置基本参数!")

          # 将 location 分解为 building, column, layer
          building = location // 10000  # 取前两位
          remaining = location % 10000  # 剩余部分为后四位
          column = remaining // 100  # 取中间两位
          layer = remaining % 100  # 取最后两位

          if building > settings.building:
               _logger.error(f"栋参数 {building} 超出最大允许值 {settings.building} ！")
               raise UserError(f"栋参数 {building} 超出最大允许值 {settings.building} ！")
          if column > settings.column:
               _logger.error(f"Column {column} 超出最大允许值 {settings.column} ！")
               raise UserError(f"Column {column} 超出最大允许值 {settings.column} ！")
          if layer > settings.layer:
               _logger.error(f"Layer {layer} 超出最大允许值 {settings.layer} !")
               raise UserError(f"Layer {layer} 超出最大允许值 {settings.layer} !")

          return building, column, layer

     def create_location_record(self):
          # building, column, layer = self.location_disintegrate(30911)
          # _logger.info(f"Decomposed values: Building={building}, column={column}, Layer={layer}")
          # 获取最后一条记录
          last_record = self.search([], order='id desc', limit=1)
          if not last_record:
               _logger.error("未找到任何记录")
               raise UserError("未找到任何记录")

          # 获取 warehouse.settings 配置
          settings = self.env['warehouse.settings'].search([], limit=1)
          if not settings:
               _logger.error("未找到参数，请先设置基本参数")
               raise UserError("未找到参数，请先设置基本参数")

          # 如果没有记录，初始化 location_number 为 10101
          if not last_record:
               new_location = 10101
               self.create({
                    'location_number': new_location,
               })
               _logger.info(f"初始化新库位编号: {new_location}")

          print(last_record.location_number)
          if last_record.location_number != 0:
               # 分解 location_number
               base_number = last_record.base_number
               location = last_record.location_number
               building = location // 10000  # 取前两位
               remaining = location % 10000  # 剩余部分为后四位
               column = remaining // 100  # 取中间两位
               layer = remaining % 100  # 取最后两位
               # 层递增
               layer += 1
               if layer > settings.layer:
                    layer = 0
                    column += 1

               if column > settings.column:
                    column = 0
                    building += 1

               base_number += 1

               if building > settings.building:
                    _logger.warning("已达到最大库位编号限制，无法继续创建")
                    raise UserError("已达到最大库位编号限制，无法继续创建")

               # 重新组合成新的 location_number
               new_location = building * 10000 + column * 100 + layer
               # 创建新记录
               self.create({
                    'goods_status': False,
                    'goods_cancel': False,
                    'fixed_pack_number': False,
                    'fixed_pack_barcode': False,
                    'pack_number': 0,
                    'base_number': base_number,
                    'location_number': new_location,
                    'pack_barcode': '',
                    })
               _logger.info(f"Created new location: {new_location}")



     def batch_create_location_records(self):
          # 获取设定数据
          settings = self.env['warehouse.settings'].search([], limit=1)
          max_building = settings.building
          max_column = settings.column
          max_layer = settings.layer
          print(f" Max : {max_building,max_column,max_layer}")
          # 获取最后一条记录
          last_record = self.search([], order='id desc', limit=1)
          location = last_record.location_number
          building, column, layer = self.location_disintegrate(location)
          print(f" Now : {building, column, layer}")
          # 判断是否超出最大限制
          if building > max_building or column > max_column or layer > max_layer:
               raise UserError("库位编号超过仓库设置的最大限制！")
               # 循环创建库位记录
          while not (building == max_building and column == max_column and layer == max_layer):
               self.create_location_record()
               # 更新当前编号（假设 create_location_record 会自动递增编号）
               last_record = self.search([], order='id desc', limit=1)
               location = last_record.location_number
               building, column, layer = self.location_disintegrate(location)
               print(building, column, layer)
          return


     def action_view_details(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'res_model': 'warehouse.location.information',
               'res_id': self.id,
               'view_mode': 'form',
               'target': 'current',  # 或 'new' 表示在弹窗打开
          }
