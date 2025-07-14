# -*- coding: utf-8 -*-
import logging
from email.policy import default

import odoo
from odoo import models, fields, api, SUPERUSER_ID
import threading
from odoo import http
from odoo.addons.test_convert.tests.test_env import record
from odoo.exceptions import UserError
from odoo.http import request
import struct
from apscheduler.schedulers.background import BackgroundScheduler
from odoo.api import readonly
from odoo.fields import Many2one
from .plc_connect import PlcClient
# from .warehouse_communication import New_Public_PlcInterfaces

from odoo.addons.bus.models.bus import dispatch
from odoo.addons.bus.models.bus import channel_with_db

_logger = logging.getLogger(__name__)
logging.getLogger('apscheduler').setLevel(logging.WARNING)
# 初始化线程锁（全局共享）
plc_lock = threading.Lock()



class AutomaticStorageLocation(models.Model):

    _name = 'automatic.storage.location'
    _description = 'automatic storage location'


    # goods_status = fields.Boolean(string='库位有货')
    # goods_cancel = fields.Boolean(string='取消库位')
    # fixed_pack_number = fields.Boolean(string='绑定框号')
    # fixed_pack_barcode = fields.Boolean(string='绑定条码')
    # pack_number = fields.Integer(string='框号')
    # base_number = fields.Integer(string='库位编号')
    # location_number = fields.Integer(string='库位号')
    # pack_barcode = fields.Char(string='框条码')


# def read_information():
#     """读取测试-批量"""
#     # 读取库位信息例子
#     results = [
#         # 库位有货
#         {'db_number': 202,'start_address': 0, 'value_type': 'bool', 'bit_index':0},
#         # 框号
#     ]
#     for result in results:
#         # value = self.batch_read_plc(result)
#         value =  PlcClient().set_db_number_read(result)
#         return value


class ControlSystemOperate(models.Model):

    # _inherit = 'system.control'
    _name = 'control.system.operate'
    _description = 'control system operate'

    # refresh_trigger = fields.Boolean(
    #     string="视图重载",default=False,
    #     help="When set to True, triggers a view refresh via bus notification")

    workshop = fields.Char(string="车间")
    line = fields.Char(string="产线")
    machine = fields.Char(string="机台")
    emergency_stop = fields.Boolean(string="紧急停止", default=False)
    manual_control = fields.Boolean(string="手动控制")
    auto_control = fields.Boolean(string="自动控制")
    stop = fields.Boolean(string="停止")
    pause = fields.Boolean(string="暂停")
    reset = fields.Boolean(string="复位")
    store = fields.Boolean(string="存储")
    outbound = fields.Boolean(string="出库")
    return_store = fields.Boolean(string="返库")
    allow_store = fields.Boolean(string="允许入库")
    allow_outbound = fields.Boolean(string="允许出库")
    allow_return = fields.Boolean(string="允许返库")
    pack_number = fields.Integer(string='框号')
    location_number = fields.Integer(string='库位号', store=True)
    pack_barcode = fields.Char(string='框条码')
    source_target = fields.Integer(string="源目标")
    new_target = fields.Integer(string="新目标")
    entrance = fields.Selection(string='出入口',
    selection=[('entrance1', '出入口1'), ('entrance2', '出入口2')])
    status = fields.Selection([
        ('idle', '空闲'),
        ('running', '运行中'),
        ('paused', '暂停'),
        ('stopped', '停止'),
        ('emergency', '紧急停止')
    ], string="状态", default='idle')
    # 展示框号
    # show_storage_pack_number = fields.Integer(string='框号')

    storage_goods_status = fields.Boolean(string='库位有货')
    # storage_goods_status_code = Many2one('plc.storage.interface', string='库位信息')
    storage_goods_cancel = fields.Boolean(string='取消库位')
    storage_fixed_pack_number = fields.Boolean(string='绑定框号',store=True)
    storage_fixed_pack_barcode = fields.Boolean(string='绑定条码',store=True)
    storage_pack_number = fields.Integer(string='框号',store=True)
    storage_base_number = fields.Integer(string='库位编号',store=True)
    storage_location_number = fields.Integer(string='库位号',store=True)
    storage_pack_barcode = fields.Char(string='框条码',store=True)

    stacker_goods_status = fields.Boolean(string='库位有货')
    stacker_goods_cancel = fields.Boolean(string='取消库位')
    stacker_fixed_pack_number = fields.Boolean(string='绑定框号')
    stacker_fixed_pack_barcode = fields.Boolean(string='绑定条码')
    stacker_pack_number = fields.Integer(string='框号')
    stacker_base_number = fields.Integer(string='库位编号')
    stacker_location_number = fields.Integer(string='库位号')
    stacker_pack_barcode = fields.Char(string='框条码')

    entrance1_goods_status = fields.Boolean(string='库位有货')
    entrance1_goods_cancel = fields.Boolean(string='取消库位')
    entrance1_fixed_pack_number = fields.Boolean(string='绑定框号')
    entrance1_fixed_pack_barcode = fields.Boolean(string='绑定条码')
    entrance1_pack_number = fields.Integer(string='框号')
    entrance1_base_number = fields.Integer(string='库位编号')
    entrance1_location_number = fields.Integer(string='库位号')
    entrance1_pack_barcode = fields.Char(string='框条码')

    entrance2_goods_status = fields.Boolean(string='库位有货')
    entrance2_goods_cancel = fields.Boolean(string='取消库位')
    entrance2_fixed_pack_number = fields.Boolean(string='绑定框号')
    entrance2_fixed_pack_barcode = fields.Boolean(string='绑定条码')
    entrance2_pack_number = fields.Integer(string='框号')
    entrance2_base_number = fields.Integer(string='库位编号')
    entrance2_location_number = fields.Integer(string='库位号')
    entrance2_pack_barcode = fields.Char(string='框条码')

    x_dummy_widget_field = fields.Char(string='Dummy Widget Field')
    refresh_status = fields.Boolean(string='是否自动刷新')

    @api.depends('storage_goods_status')
    def _compute_one_second(self):
        pass

    @api.onchange('pack_number')
    def _onchange_pack_number(self):
        record1 = self.browse(1)
        record1.write({'pack_number': self.pack_number})
        self._compare_pack_number()
        # print('change1')
        # print(record1.pack_number)
        # print(self.pack_number)

    def _compare_pack_number(self):

        if self.pack_number != 0 :
            record_settings = self.env['warehouse.settings'].search([], limit=1)
            entrance_1 = record_settings.entrance_1
            entrance_2 = record_settings.entrance_2
            # 在 automatic.storage.location 中搜索匹配的 pack_number
            storage_record = self.env['warehouse.location.information'].search(
                [('pack_number', '=', self.pack_number)], limit=1)
            barcode_record = self.env['frame.barcode'].search(
                [('frame_number', '=', self.pack_number)], limit=1)

            record = self.browse(1)
            record.refresh_status = True
            record.write({
                'allow_store': False,
                'allow_outbound': False,
                'allow_return': False,
            })
            #如果库存中数据中没有对应的框条码，则获取框条码
            if storage_record.pack_barcode :
                record.write({
                'pack_barcode': storage_record.pack_barcode,
                })
            else:
                record.write({
                'pack_barcode': barcode_record.frame_barcode,
                })
            print('10',record.pack_barcode)
            print('11',storage_record.pack_barcode)
            # 如果能在库存里找到对应的框号，则获取库位信息
            if storage_record:
                record.write({
                    'pack_number': storage_record.pack_number,
                    'location_number': storage_record.location_number,
                })
                if storage_record.goods_status == True:
                    record.write({
                        'allow_store': False,
                        'allow_outbound': True,
                        'allow_return': False,
                    })
                    record.write({
                        'source_target': storage_record.location_number,
                        })
                    if self.entrance == False or self.entrance == 'entrance1':
                        record.write({
                        'new_target': entrance_1,
                        })
                    if self.entrance == 'entrance2':
                        record.write({
                        'new_target': entrance_2,
                        })
                else:
                    record.write({
                        'allow_store': False,
                        'allow_outbound': False,
                        'allow_return': True,
                    })
                    if self.entrance == False or self.entrance == 'entrance1':
                        record.write({
                        'source_target': entrance_1,
                        })
                    if self.entrance == 'entrance2':
                        record.write({
                        'source_target': entrance_2,
                        })
                    record.write({
                        'new_target': storage_record.location_number,
                    })

            else:
                record.write({
                    'allow_store': True,
                    'allow_outbound': False,
                    'allow_return': False,
                })
                location_record_1 = self.env['warehouse.location.information'].search(
                    [('location_number', '!=', entrance_1),
                     ('location_number', '!=', entrance_2),
                     ('location_number', '<', 20000),
                     ('goods_cancel', '=', False),
                     ('goods_status', '=', False)], limit=1)
                location_record_2 = self.env['warehouse.location.information'].search(
                    [('location_number', '!=', entrance_1),
                     ('location_number', '!=', entrance_2),
                     ('location_number', '>', 20000),
                     ('goods_cancel', '=', False),
                     ('goods_status', '=', False)], limit=1)
                     # 剩余部分为后四位
                column_layer_1 = location_record_1.location_number % 10000
                column_layer_2 = location_record_2.location_number % 10000

                if column_layer_1<column_layer_2:
                    record.write({
                        'location_number': location_record_1.location_number,
                    })
                else:
                    record.write({
                        'location_number': location_record_2.location_number,
                    })

                record.write({
                    'source_target': record.location_number,
                })

                if self.entrance == False or self.entrance == 'entrance1':
                    record.write({
                        'new_target': entrance_1,
                    })
                if self.entrance == 'entrance2':
                    record.write({
                        'new_target': entrance_2,
                    })







            # 查询模型A
            # storage_records = self.env['automatic.storage.location'].search([('pack_number', '=', self.pack_number)])
            # print(self.pack_number)
            # if storage_records:
            #     # 如果找到匹配记录，获取目标字段值
            #     # target_field = storage_records[0].pack_number
            #     print('查询到框号！')
            # else:
            #     raise UserError('没有查询到框号！')

            # 获取 automatic.storage.location 模型中的所有 pack_number 值
            # location_records = self.env['automatic.storage.location'].search([])
            # pack_numbers = [record.pack_number for record in location_records if record.pack_number]
            # print(pack_numbers)

            # 输出结果示例
            # _logger.info("Pack Numbers: %s", pack_numbers)


    def initialize_data(self):
        record = self.env['scheduler'].search([()])
        record.start()
        pass

    def start_plc_scheduler(self):
        _logger.info("开始启动定时任务测试")
        pass


    def batch_read_plc(self, row_data):
        """
        通用数据读取方法
        :param row_data: plc.data 记录集
        :return: value 读取结果
        """
        value = PlcClient().set_db_number_read(row_data)
        # _logger.info(f'{row_data.get("value_type")}查询结果：{value}')
        return value

    def storage_information_write(self):
        """传递到PLC进行写入"""
        # 单独写入
        # 库位有货
        # read_storage_goods_status = self.storage_goods_status
        # data = {
        #     'value' : read_storage_goods_status,
        #     'bit_index': 0,
        #     'value_type' : 'bool',
        # }
        # PlcClient().set_db_number_write(data)
        # # 取消库位
        # read_storage_goods_cancel = self.storage_goods_cancel
        # if read_storage_goods_cancel == None:
        #     read_storage_goods_cancel = False
        # data = {
        #     'value': read_storage_goods_cancel,
        #     'bit_index': 2,
        #     'value_type': 'bool'
        # }
        # PlcClient().set_db_number_write(data)
        # # 框号
        # read_storage_pack_number = self.storage_pack_number
        # data = {
        #     'value': read_storage_pack_number,
        #     'offset': 2,
        #     'value_type': 'int'
        # }
        # PlcClient().set_db_number_write(data)
        # # 库位编号
        # read_storage_base_number = self.storage_base_number
        # data = {
        #     'value': read_storage_base_number,
        #     'offset': 4,
        #     'value_type': 'int'
        # }
        # PlcClient().set_db_number_write(data)
        # # 库位号
        # read_storage_location_number = self.storage_location_number
        # data = {
        #     'value': read_storage_location_number,
        #     'offset': 6,
        #     'value_type': 'int'
        # }
        # PlcClient().set_db_number_write(data)
        # 框条码
        stacker_pack_barcode = 'pk' + str(self.stacker_pack_barcode)
        #stacker_pack_barcode = 'pl1255'
        _logger.info(stacker_pack_barcode)

        # data = {
        #     'value': stacker_pack_barcode,
        #     'offset': 14,
        #     "string_max_len": 8,
        #     'value_type': 'string',
        #     "db_number": 262
        # }
        # PlcClient().set_db_number_write(data)
        # 对某个DB内进行批量写入

    # @api.model
    def storage_information_read(self):
        """读取测试-批量"""
        results = [
            # 库位有货，框号，库位号，框条码
            {'db_number': 262, 'offset': 0, 'value_type': 'bool', 'bit_index': 0},
            {'db_number': 262, 'offset': 2, 'value_type': 'int'},
            {'db_number': 262, 'offset': 4, 'value_type': 'int'},
            {'db_number': 262, 'offset': 10, 'value_type': 'dint'},
            {'db_number': 262, 'offset': 14, 'value_type': 'string', "string_max_len": 18},
        ]
        num = 0
        values_to_write = {}
        for result in results:
            num += 1
            value = self.batch_read_plc(result)
            # _logger.info(type(value))
            if num == 1:
                # self.storage_goods_status = value
                values_to_write['storage_goods_status'] = value
                # values_to_write['refresh_trigger'] = value
            elif num == 2:
                # self.storage_pack_number = value
                values_to_write['storage_base_number'] = value
            elif num == 3:
                # self.storage_pack_number = value
                values_to_write['storage_pack_number'] = value
                # self.env['control.system.operate'].browse(1).write({'storage_pack_number': value})
            elif num == 4:
                values_to_write['storage_location_number'] = value
            elif num == 5:
                values_to_write['storage_pack_barcode'] = value

        # 统一写入数据库，减少 I/O 次数
        if values_to_write:
            record = self.browse(1)
            record.write(values_to_write)




    def stacker_information_read(self):
        """读取测试-批量"""
        results = [
            #库位有货，框号，库位号，框条码
            {'db_number': 262, 'offset': 36, 'value_type': 'bool', 'bit_index':0},
            {'db_number': 262, 'offset': 38, 'value_type': 'int'},
            {'db_number': 262, 'offset': 40, 'value_type': 'int'},
            {'db_number': 262, 'offset': 46, 'value_type': 'dint'},
            {'db_number': 262, 'offset': 50, 'value_type': 'string', "string_max_len": 18},
        ]
        num = 0
        values_to_write = {}
        for result in results:
            num += 1
            value = self.batch_read_plc(result)
            # _logger.info(type(value))
            if num == 1:
                values_to_write['stacker_goods_status'] = value

            elif num == 2:
                values_to_write['stacker_base_number'] = value
            elif num == 3:
                values_to_write['stacker_pack_number'] = value
            elif num == 4:
                values_to_write['stacker_location_number'] = value
            elif num == 5:
                values_to_write['stacker_pack_barcode'] = value
        if values_to_write:
            record = self.browse(1)
            record.write(values_to_write)

    def entrance1_information_read(self):
        """读取测试-批量"""
        results = [
            #库位有货，框号，库位号，框条码
            {'db_number': 262, 'offset': 72, 'value_type': 'bool', 'bit_index':0},
            {'db_number': 262, 'offset': 74, 'value_type': 'int'},
            {'db_number': 262, 'offset': 76, 'value_type': 'int'},
            {'db_number': 262, 'offset': 82, 'value_type': 'dint'},
            {'db_number': 262, 'offset': 86, 'value_type': 'string', "string_max_len": 18},
        ]
        num = 0
        values_to_write = {}
        for result in results:
            num += 1
            value = self.batch_read_plc(result)
            # _logger.info(type(value))
            if num == 1:
                values_to_write['entrance1_goods_status'] = value
            elif num == 2:
                values_to_write['entrance1_base_number'] = value
            elif num == 3:
                values_to_write['entrance1_pack_number'] = value
            elif num == 4:
                values_to_write['entrance1_location_number'] = value
            elif num == 5:
                values_to_write['entrance1_pack_barcode'] = value
        if values_to_write:
            record = self.browse(1)
            record.write(values_to_write)

    def entrance2_information_read(self):
        """读取测试-批量"""
        results = [
            #库位有货，框号，库位号，框条码
            {'db_number': 262, 'offset': 108, 'value_type': 'bool', 'bit_index':0},
            {'db_number': 262, 'offset': 110, 'value_type': 'int'},
            {'db_number': 262, 'offset': 112, 'value_type': 'int'},
            {'db_number': 262, 'offset': 118, 'value_type': 'dint'},
            {'db_number': 262, 'offset': 122, 'value_type': 'string', "string_max_len": 18},
        ]
        num = 0
        values_to_write = {}
        for result in results:
            num += 1
            value = self.batch_read_plc(result)
            if num == 1:
                values_to_write['entrance2_goods_status'] = value
            elif num == 2:
                values_to_write['entrance2_base_number'] = value
            elif num == 3:
                values_to_write['entrance2_pack_number'] = value
            elif num == 4:
                values_to_write['entrance2_location_number'] = value
            elif num == 5:
                values_to_write['entrance2_pack_barcode'] = value
        if values_to_write:
            record = self.browse(1)
            record.write(values_to_write)

    def emergency_button(self):
        # code = self.env['system.control']

        self.write({'emergency_stop': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',  # 强制刷新当前视图
        }

    def manual_button(self):
        for record in self:
            record.manual_control = True
            record.auto_control = False

    def auto_button(self):
        for record in self:
            record.manual_control = False
            record.auto_control = True

    def stop_button(self):
        for record in self:
            record.emergency_stop = not record.emergency_stop

    def pause_button(self):
        for record in self:
            record.emergency_stop = not record.emergency_stop

    def reset_button(self):
        for record in self:
            record.emergency_stop = not record.emergency_stop

    def store_button(self):
        for record in self:
            record.store = not record.store

    def outbound_button(self):
        for record in self:
            record.outbound = not record.outbound

    def return_store_button(self):
        for record in self:
            record.return_store = not record.return_store






