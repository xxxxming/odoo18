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


