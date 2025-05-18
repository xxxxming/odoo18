# -*- coding: utf-8 -*-

import snap7

from odoo import models, fields, api

class WarehouseProperty(models.Model):
     _name = 'warehouse.property'
     _description = 'warehouse property'
     _order = 'id desc'
     name = fields.Char(string='名称')
     state = fields.Selection(string='状态',selection=[('new','新任务'),('in_progress','执行中'),('canceled','取消'),('done','完成')])
     inventory_action = fields.Selection(string='操作',selection=[('store','入库'),('Outbound','出库'),('return','返库')])
     source_target = fields.Integer(string='源目标')
     new_target = fields.Integer(string='新目标')
     frame_number = fields.Integer(string='框号')
     pack_barcode = fields.Char(string='框条码')

# class asrs01(models.Model):
#     _name = 'asrs01.asrs01'
#     _description = 'asrs01.asrs01'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
