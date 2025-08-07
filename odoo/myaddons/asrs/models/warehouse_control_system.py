# -*- coding: utf-8 -*-
from odoo import models, fields, api

from .plc_connect import PlcClient






class WarehouseControlSystem(models.Model):

     _name = 'warehouse.control.system'
     _description = 'warehouse control system'


     # life = fields.Boolean(string="心跳符号")
     # ready = fields.Boolean(string="准备就绪")
     factory = fields.Char(string="工厂代号")
     workshop = fields.Char(string="车间代号")
     line = fields.Char(string="线体代号")
     machine = fields.Char(string="机台代号")

     netcontrol = fields.Boolean(string='网络控制')
     pccontrol = fields.Boolean(string='PC控制')
     alarm = fields.Boolean(string='报警')
     ready = fields.Boolean(string='就绪')
     hardware_ready = fields.Boolean(string='硬件就绪')
     auto_ready = fields.Boolean(string='自动就绪')
     auto_take_finish = fields.Boolean(string='取料完成')
     auto_feed_finish = fields.Boolean(string='送料完成')
     auto_source_position = fields.Boolean(string='到达源目标')
     auto_target_position = fields.Boolean(string='到达新目标')
     auto_finish = fields.Boolean(string='自动完成')
     auto_state = fields.Boolean(string='自动状态')
     none1 = fields.Boolean(string='无1')
     none2 = fields.Boolean(string='无2')
     estate = fields.Integer(string='状态')

     # 添加关联到输入输出信号的字段
     input_ids = fields.One2many('warehouse.control.system.input', 'wcs_id', string='输入信号')
     output_ids = fields.One2many('warehouse.control.system.output', 'wcs_id', string='输出信号')




     def control_system_read_write(self):
         self.automation_state_read()


     def automation_state_read(self):

        results = [
            {'db_number': 260, 'offset': 40, 'bit_index': 0, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 40, 'bit_index': 1, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 40, 'bit_index': 2, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 40, 'bit_index': 3, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 40, 'bit_index': 4, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 40, 'bit_index': 5, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 40, 'bit_index': 6, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 40, 'bit_index': 7, 'value_type': 'bool'},

            {'db_number': 260, 'offset': 41, 'bit_index': 0, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 41, 'bit_index': 1, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 41, 'bit_index': 2, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 41, 'bit_index': 3, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 41, 'bit_index': 4, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 41, 'bit_index': 5, 'value_type': 'bool'},
            {'db_number': 260, 'offset': 44, 'value_type': 'int'},
        ]
        num = 0
        values_to_write = {}
        for result in results:
            num += 1
            # value = PlcClient().db_number_read(result)
            value = PlcClient().db_number_read(result)
            if num == 1:
                values_to_write['netcontrol'] = value
            elif num == 2:
                values_to_write['pccontrol'] = value
            elif num == 3:
                values_to_write['alarm'] = value
            elif num == 4:
                values_to_write['ready'] = value
            elif num == 5:
                values_to_write['hardware_ready'] = value
            elif num == 6:
                values_to_write['auto_ready'] = value
            elif num == 7:
                values_to_write['auto_take_finish'] = value
            elif num == 8:
                values_to_write['auto_feed_finish'] = value
            elif num == 9:
                values_to_write['auto_source_position'] = value
            elif num == 10:
                values_to_write['auto_target_position'] = value
            elif num == 11:
                values_to_write['auto_finish'] = value
            elif num == 12:
                values_to_write['auto_state'] = value
            elif num == 13:
                values_to_write['none1'] = value
            elif num == 14:
                values_to_write['none2'] = value
            elif num == 15:
                values_to_write['estate'] = value
                # print(value)
        if values_to_write:
            record = self.browse(6)
            record.write(values_to_write)

     def start_auto_refresh(self):
         self.env['warehouse.plc.task'].start_scheduler()

     def stop_auto_refresh(self):
         self.env['warehouse.plc.task'].stop_scheduler()


































class WarehouseControlSystemInput(models.Model):
    _name = 'warehouse.control.system.input'
    _description = 'Warehouse Control System Input Signals'

    name = fields.Char(string="信号名称", required=True)
    address = fields.Char(string="地址", required=True)  # 如 I0.0, I0.1等
    value = fields.Boolean(string="值")
    wcs_id = fields.Many2one('warehouse.control.system', string="控制系统", ondelete='cascade')


class WarehouseControlSystemOutput(models.Model):
    _name = 'warehouse.control.system.output'
    _description = 'Warehouse Control System Output Signals'

    name = fields.Char(string="信号名称", required=True)
    address = fields.Char(string="地址", required=True)  # 如 Q0.0, Q0.1等
    value = fields.Boolean(string="状态")
    wcs_id = fields.Many2one('warehouse.control.system', string="控制系统", ondelete='cascade')











































