from email.policy import default
from operator import truediv

from xlwt.ExcelFormulaLexer import false_pattern

from odoo import models,fields,api
from datetime import timedelta

class EstatesProperty(models.Model):
    _name = 'estate.property.tag'
    _description = '房产标签'
    _order = 'name'

    name = fields.Char(string="房产标签",required=True)
    color = fields.Integer(string="颜色",default=10)
    _sql_constraints = [('name_unique', 'UNIQUE(name)', '房屋标签必须唯一.')]

