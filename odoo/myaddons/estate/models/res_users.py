from odoo import models,fields,api

class ResUsers(models.Model):
    _inherit = 'res.users'
    property_ids = fields.One2many('estate.property','seller_id',string='我的房产',domain = ['|',('state','=','new'),('state','=','offer_received')])
