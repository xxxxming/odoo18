# -*- coding: utf-8 -*-

from odoo import models, fields, api

class WarehouseLocationInformation(models.Model):
     _name = 'warehouse.location.information'
     _description = 'warehouse location information'
     goods_status = fields.Boolean(string='库位有货')
     goods_cancel = fields.Boolean(string='取消库位')
     fixed_pack_number = fields.Boolean(string='绑定框号')
     fixed_pack_barcode = fields.Boolean(string='绑定条码')
     pack_number = fields.Integer(string='框号')
     base_number = fields.Integer(string='库位编号')
     location_number = fields.Integer(string='库位号')
     pack_barcode = fields.Char(string='框条码')


# @api.model
# def create(self, vals_list):
#      # 如果传入的是单个字典，则将其转换为列表
#      if isinstance(vals_list, dict):
#           vals_list = [vals_list]
#
#      records = self.env['warehouse.location.information']
#      for vals in vals_list:
#           # 在这里添加自定义逻辑
#           vals['base_number'] = self.env['ir.sequence'].next_by_code('warehouse.location.information')
#           record = super(WarehouseLocationInformation, self).create(vals)
#           records += record
#
#      return records














