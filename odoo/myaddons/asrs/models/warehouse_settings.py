# -*- coding: utf-8 -*-
from odoo import models, fields, api

class WarehouseSettings(models.Model):

     _name = 'warehouse.settings'
     _description = 'Warehouse settings'

     warehouse_name = fields.Char(string='仓库名称')
     building = fields.Integer(string='栋数')
     column = fields.Integer(string='列数')
     layer = fields.Integer(string='层数')


     layer_spacing = fields.Float(string='层间距')
     column_spacing = fields.Float(string='列间距')
     total_locations = fields.Integer(string='库位总数',compute='_compute_total_locations',store=True)

     @api.depends('building','column','layer')
     def _compute_total_locations(self):
          for record in self:
               record.total_locations = record.building * record.column * record.layer



