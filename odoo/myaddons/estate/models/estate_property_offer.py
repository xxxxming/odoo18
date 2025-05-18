from email.policy import default
from operator import truediv

# from win32comext.shell.demos.IUniformResourceLocator import property_ids
# from xlwt.ExcelFormulaLexer import false_pattern

from odoo import models,fields,api
from datetime import timedelta

class EstatesPropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = '房屋报价'
    _order = 'price desc'

    price = fields.Float(string='价格')
    status = fields.Selection(string='报价状态',selection=[('Accepted','接受报价'),('Refused','拒绝报价')],copy=False)
    partner_id = fields.Many2one('res.partner',string='买家',required=True)
    property_id = fields.Many2one('estate.property',string='房产',required=True)

    validity = fields.Integer(string='有效期',default=7)
    date_deadline = fields.Date(string='截止日期',compute='_compute_date_deadline',inverse='_inverse_date_deadline')

    property_type_id = fields.Many2one(related='property_id.property_type_id',store=True)

    _sql_constraints = [
        ('check_price', 'CHECK(price >= 0 )', '报价价格必须严格为正数.')
    ]

    @api.depends('create_date','validity')
    def _compute_date_deadline(self):
        for record in self:
            if record.create_date:
                record.date_deadline = record.create_date + timedelta(days=record.validity)
            else:
                record.date_deadline = fields.Date.today() + timedelta(days=record.validity)
    def _inverse_date_deadline(self):
        for record in self:
            if record.create_date:
                 record.validity = (record.date_deadline - record.create_date.date()).days

    def do_accept(self):
        for record in self:
            record.status = 'Accepted'
            record.property_id.state = 'offer_accepted'
            record.property_id.selling_price = record.price
            record.property_id.buyer_id = record.partner_id

    def do_refuse(self):
        for record in self:
            record.status = 'Refused'

    # @api.model
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
                property_id = vals.get('property_id')
                property = self.env['estate.property'].browse(property_id)
                property.state='offer_received'

                price = vals.get('price')
                if price <= property.best_price:
                    raise models.ValidationError('新报价必须高于现有报价')

                return super().create(vals)

