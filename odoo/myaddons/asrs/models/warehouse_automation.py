# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError

class WarehouseAutomation(models.Model):
     _name = 'warehouse.automation'
     _description = 'warehouse automation'

     creation_date = fields.Date(string="日期")
     reference_number = fields.Char(string="参考号")
     pack_number = fields.Integer(string='框号')
     source_target = fields.Integer(string="源目标")
     new_target = fields.Integer(string="新目标")
     entrance = fields.Selection(string='出入口',selection=[('none', '无'),('entrance1', '出入口1'),('entrance2', '出入口2')])
     order_mode = fields.Selection(string='订单',selection=[('immediately', '立即执行'),('manual', '手动执行'),('lineUp', '列队执行')])
     inventory_action = fields.Selection(string='操作',selection=[('store', '入库'),('Outbound', '出库'),('return', '返库'),('moving','移库')])
     order_status = fields.Selection( string="状态",selection=[('new', '新订单'),('waiting', '等待中'),('running', '执行中'),('cancel', '取消'), ('finish', '已完成')])