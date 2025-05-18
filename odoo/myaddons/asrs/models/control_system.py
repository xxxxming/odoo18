# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ControlSystem(models.Model):
     _name = 'control.system'
     _description = 'inventory control system'
     # life = fields.Boolean(string="心跳符号")
     # ready = fields.Boolean(string="准备就绪")
     factory = fields.Char(string="工厂代号")
     workshop = fields.Char(string="车间代号")
     line = fields.Char(string="线体代号")
     machine = fields.Char(string="机台代号")

     input_I00 = fields.Boolean(string="输入I0.0")
     input_I01 = fields.Boolean(string="输入I0.1")
     input_I02 = fields.Boolean(string="输入I0.2")
     input_I03 = fields.Boolean(string="输入I0.3")
     input_I04 = fields.Boolean(string="输入I0.4")
     input_I05 = fields.Boolean(string="输入I0.5")
     input_I06 = fields.Boolean(string="输入I0.6")
     input_I07 = fields.Boolean(string="输入I0.7")

     input_I10 = fields.Boolean(string="输入I1.0")
     input_I11 = fields.Boolean(string="输入I1.1")
     input_I12 = fields.Boolean(string="输入I1.2")
     input_I13 = fields.Boolean(string="输入I1.3")
     input_I14 = fields.Boolean(string="输入I1.4")
     input_I15 = fields.Boolean(string="输入I1.5")
     input_I16 = fields.Boolean(string="输入I1.6")
     input_I17 = fields.Boolean(string="输入I1.7")

     output_Q00 = fields.Boolean(string="输出Q0.0")
     output_Q01 = fields.Boolean(string="输出Q0.1")
     output_Q02 = fields.Boolean(string="输出Q0.2")
     output_Q03 = fields.Boolean(string="输出Q0.3")
     output_Q04 = fields.Boolean(string="输出Q0.4")
     output_Q05 = fields.Boolean(string="输出Q0.5")
     output_Q06 = fields.Boolean(string="输出Q0.6")
     output_Q07 = fields.Boolean(string="输出Q0.7")

     output_Q10 = fields.Boolean(string="输出Q1.0")
     output_Q11 = fields.Boolean(string="输入Q1.1")
     output_Q12 = fields.Boolean(string="输入Q1.2")
     output_Q13 = fields.Boolean(string="输入Q1.3")
     output_Q14 = fields.Boolean(string="输入Q1.4")
     output_Q15 = fields.Boolean(string="输入Q1.5")
     output_Q16 = fields.Boolean(string="输入Q1.6")
     output_Q17 = fields.Boolean(string="输入Q1.7")





















