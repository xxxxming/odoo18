from email.policy import default
from operator import truediv

from xlwt.ExcelFormulaLexer import false_pattern

from odoo import models,fields,api
from datetime import timedelta

class EstatesProperty(models.Model):
    _name = 'estate.property.type'
    _description = '房产买卖'
    _order = 'name'

    name = fields.Char(string="房产类型",required=True)
    property_ids = fields.One2many('estate.property','property_type_id',string="房产")
    sequence = fields.Integer(string="顺序",default=10)
    offer_ids = fields.One2many('estate.property.offer', 'property_type_id', string="报价")
    offer_count = fields.Integer(string="报价数量", compute='_compute_offer_count')

    _sql_constraints = [('name_unique', 'UNIQUE(name)', '房屋类型必须唯一.')]

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)