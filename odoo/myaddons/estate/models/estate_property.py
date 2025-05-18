from email.policy import default
from operator import truediv
from pickle import FALSE

from xlwt.ExcelFormulaLexer import false_pattern
from odoo import models,fields,api
from datetime import timedelta

import odoo
from odoo.exceptions import ValidationError

class EstatesProperty(models.Model):
    _name = 'estate.property'
    _description = 'Estate Property'
    _order = 'id desc'
    name = fields.Char(string="名称",required=True)
    description = fields.Text(string="描述")
    postcode = fields.Char(string="邮编")
    date_availability = fields.Date(string="可售日期",copy=False,default=lambda self:fields.Date.today()+timedelta(days=90))
    expected_price = fields.Float(string="期望价格",required=True)
    selling_price = fields.Float(string="售价",readonly=True,copy=False)
    bedrooms = fields.Integer(string="卧室数量",default=2)
    living_area = fields.Integer(string="使用面积")
    facades = fields.Integer(string="立面数量")
    garage = fields.Boolean(string="车库")
    garden = fields.Boolean(string="花园")
    garden_area = fields.Integer(string="花园面积")
    garden_orientation = fields.Selection(string="花园朝向",selection=
        [('north', '北'), ('south', '南'), ('east', '东'), ('west', '西')])
    active = fields.Boolean(string="是否归档",default=True)
    state = fields.Selection(string="状态",selection=[('new', '新订单'), ('offer_received', '收到报价'), ('offer_accepted', '接受报价'), ('sold', '售出'), ('canceled', '取消')],
                              required=True,default='new',copy=False)
    property_type_id = fields.Many2one('estate.property.type',string="房产类型")
    buyer_id = fields.Many2one('res.partner',string="买家",copy=False)
    seller_id = fields.Many2one('res.users',string="卖家",default=lambda self:self.env.user)
    tag_ids = fields.Many2many('estate.property.tag',string="房屋标签")
    offer_ids = fields.One2many('estate.property.offer','property_id',string="报价")
    total_price = fields.Float(string="总价",compute='_compute_total_price')
    best_price= fields.Float(string="最高报价",compute='_compute_best_price')

    _sql_constraints = [
        ('check_expected_price', 'CHECK(expected_price > 0 )','房产预期价格必须严格为正数.'),
        ('check_selling_price', 'CHECK(selling_price > 0 )', '房产售价必须为正数.'),
    ]

    @api.constrains('selling_price','expected_price')
    def _check_price(self):
        for record in self:
            if record.selling_price and record.expected_price:
                if record.selling_price < record.expected_price * 0.9:
                    raise ValidationError("销售价格必须大于等于期望价格的90%")

    # @api def _compute_total_price(self):
    #     for record in self:
    #         record.total_price = record.living_area + record.garden_area


    @api.depends('living_area','garden_area')
    def _compute_total_price(self):
        for record in self:
            record.total_price = record.living_area  + record.garden_area

    @api.depends('offer_ids.price')
    # def _compute_best_price(self):
    #     for record in self:
    #         record.best_price = max(record.offer_ids.mapped('price'))
    def _compute_best_price(self):
        for record in self:
            if record.offer_ids:  # 检查是否存在offer_ids
                record.best_price = max(record.offer_ids.mapped('price'))
            else:
                record.best_price = 0  # 如果为空，设置默认值为0

    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = 0
            self.garden_orientation = False

    @api.onchange('garage')
    def _onchange_garage(self):
        if self.garage:
            return {
                'warning': {
                    'title': '警告',
                    'message': 'Garage is a new feature, be careful',
                }
            }

    def do_sold(self):
        for record in self:
            if record.state != 'canceled':
                record.state = 'sold'

    def do_canceled(self):
        for record in self:
            if record.state != 'sold':
                record.state = 'canceled'

    @api.ondelete(at_uninstall=False)
    def _unlink_except_sold(self):
        for record in self:
            if record.state not in ['new','canceled']:
                raise odoo.exceptions.UserError("只有新建和取消状态的房产才能删除")



