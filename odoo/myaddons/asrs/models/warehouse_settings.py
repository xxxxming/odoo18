# -*- coding: utf-8 -*-

from odoo import models, fields, api

class WarehouseSettings(models.Model):
     _name = 'warehouse.settings'
     _description = 'Warehouse settings'
     number_layers  = fields.Integer(string='层数')
     number_column = fields.Integer(string='列数')
     lift_coordinate = fields.Float(string='提升机坐标')
     layer_spacing = fields.Float(string='层间距')
     shuttle_coordinate = fields.Float(string='穿梭机坐标')
     column_spacing = fields.Float(string='列间距')






