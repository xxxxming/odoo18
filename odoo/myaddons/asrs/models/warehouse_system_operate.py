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


    goods_status = fields.Boolean(string='库位有货')
    goods_cancel = fields.Boolean(string='取消库位')
    fixed_pack_number = fields.Boolean(string='绑定框号')
    fixed_pack_barcode = fields.Boolean(string='绑定条码')
    pack_number = fields.Integer(string='框号')
    base_number = fields.Integer(string='库位编号')
    location_number = fields.Integer(string='库位号')
    pack_barcode = fields.Char(string='框条码')


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


class WarehouseSystemOperate(models.Model):

    # _inherit = 'system.control'
    _name = 'warehouse.system.operate'
    #_name = 'control.system.operate'
    _description = 'warehouse system operate'

    # refresh_trigger = fields.Boolean(
    #     string="视图重载",default=False,
    #     help="When set to True, triggers a view refresh via bus notification")

    workshop = fields.Char(string="车间",default='车间1')
    line = fields.Char(string="产线")
    machine = fields.Char(string="机台")
    emergency_stop = fields.Boolean(string="紧急停止", default=False)
    manual_auto_control = fields.Boolean(string="手动自动")
    start = fields.Boolean(string="启动")
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
    base_number = fields.Integer(string='序号')
    location_number = fields.Integer(string='库位号')
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
    storage_base_number = fields.Integer(string='序号',store=True)
    storage_location_number = fields.Integer(string='库位号',store=True)
    storage_pack_barcode = fields.Char(string='框条码',store=True)

    stacker_goods_status = fields.Boolean(string='库位有货')
    stacker_goods_cancel = fields.Boolean(string='取消库位')
    stacker_fixed_pack_number = fields.Boolean(string='绑定框号')
    stacker_fixed_pack_barcode = fields.Boolean(string='绑定条码')
    stacker_pack_number = fields.Integer(string='框号')
    stacker_base_number = fields.Integer(string='序号')
    stacker_location_number = fields.Integer(string='库位号')
    stacker_pack_barcode = fields.Char(string='框条码')

    entrance1_goods_status = fields.Boolean(string='库位有货')
    entrance1_goods_cancel = fields.Boolean(string='取消库位')
    entrance1_fixed_pack_number = fields.Boolean(string='绑定框号')
    entrance1_fixed_pack_barcode = fields.Boolean(string='绑定条码')
    entrance1_pack_number = fields.Integer(string='框号')
    entrance1_base_number = fields.Integer(string='序号')
    entrance1_location_number = fields.Integer(string='库位号')
    entrance1_pack_barcode = fields.Char(string='框条码')

    entrance2_goods_status = fields.Boolean(string='库位有货')
    entrance2_goods_cancel = fields.Boolean(string='取消库位')
    entrance2_fixed_pack_number = fields.Boolean(string='绑定框号')
    entrance2_fixed_pack_barcode = fields.Boolean(string='绑定条码')
    entrance2_pack_number = fields.Integer(string='框号')
    entrance2_base_number = fields.Integer(string='序号')
    entrance2_location_number = fields.Integer(string='库位号')
    entrance2_pack_barcode = fields.Char(string='框条码')

    x_dummy_widget_field = fields.Char(string='Dummy Widget Field')
    refresh_status = fields.Boolean(string='是否自动刷新')

    @api.depends('storage_goods_status')
    def _compute_one_second(self):
        pass

    @api.onchange('entrance')
    def _onchange_entrance(self):
        self._compare_pack_number()
        self.command_data_write()

    @api.onchange('pack_number')
    def _onchange_pack_number(self):
        record1 = self.browse(1)
        record1.write({'pack_number': self.pack_number})
        self._compare_pack_number()
        self.command_data_write()
        record.refresh_status = True

    def _compare_pack_number(self):

        if self.pack_number != 0 :
            record_settings = self.env['warehouse.settings'].search([], limit=1)
            entrance_1 = record_settings.entrance_1
            entrance_2 = record_settings.entrance_2
            # 在 automatic.storage.location 中搜索匹配的 pack_number
            storage_record = self.env['warehouse.location.information'].search(
                [('pack_number', '=', self.pack_number)], limit=1)
            barcode_record = self.env['warehouse.frame.barcode'].search(
                [('frame_number', '=', self.pack_number)], limit=1)

            record = self.browse(1)

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
                    'new_target': record.location_number,
                })

                if self.entrance == False or self.entrance == 'entrance1':
                    record.write({
                        'source_target': entrance_1,
                    })
                if self.entrance == 'entrance2':
                    record.write({
                        'source_target': entrance_2,
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

    def _compare_pack_barcode(self):
        if not self.pack_barcode:
            print(self.pack_barcode)





    def command_data_write(self):
        record = self.browse(1)
        entrance = 0
        allow_store = record.allow_store
        allow_outbound = record.allow_outbound
        allow_return = record.allow_return
        pack_number = record.pack_number
        base_number = record.base_number
        source_target = record.source_target
        new_target = record.new_target
        location_number = record.location_number
        pack_barcode = record.pack_barcode
        if record.entrance == False or record.entrance == 'entrance1':
            entrance = 1
        if record.entrance == 'entrance2':
            entrance = 2
        # plc_client = PlcClient()
        try:
            # 批量写入
            data_list = [
                {'value': allow_store, "db_number": 260, 'offset': 2, 'bit_index': 3, 'value_type': 'bool'},
                {'value': allow_outbound, "db_number": 260, 'offset': 2, 'bit_index': 4, 'value_type': 'bool'},
                {'value': allow_return, "db_number": 260, 'offset': 2, 'bit_index': 5, 'value_type': 'bool'},
                {'value': entrance,"db_number": 260,'offset': 4,'value_type': 'int'},
                {'value': pack_number,"db_number": 260,'offset': 6,'value_type': 'int'},
                {'value': base_number, "db_number": 260, 'offset': 8, 'value_type': 'int'},
                {'value': source_target, "db_number": 260, 'offset': 10, 'value_type': 'int'},
                {'value': new_target, "db_number": 260, 'offset': 12, 'value_type': 'int'},
                {'value': location_number,"db_number": 260,'offset': 14,'value_type': 'dint'},
                {'value': pack_barcode,"db_number": 260,'offset': 18,"string_max_len": 18,'value_type': 'string'}
            ]
            for data in data_list:
                PlcClient().db_number_write(data)
        except Exception as e:
            _logger.error(f"库位信息写入失败！: {str(e)}")
            raise

    def initialize_data(self):
        record = self.env['scheduler'].search([()])
        record.start()
        pass

    def start_plc_scheduler(self):
        _logger.info("开始启动定时任务测试")
        pass

    def control_system_read_write(self):
        # self.storage_information_write()
        self.storage_information_read()
        self.stacker_information_read()
        self.entrance1_information_read()
        self.entrance2_information_read()

    def storage_information_write(self):
        """传递到PLC进行写入"""
        # 提取字段值
        storage_goods_status = self.storage_goods_status
        storage_base_number = self.storage_base_number
        storage_pack_number = self.storage_pack_number
        storage_location_number = self.storage_location_number
        storage_pack_barcode = self.storage_pack_barcode
        print('1',storage_pack_barcode)
        print('2',self.storage_pack_barcode)
        # plc_client = PlcClient()
        try:
            # 批量写入
            data_list = [
                {'value': storage_goods_status,"db_number": 262,'offset': 0,'bit_index': 0,'value_type': 'bool'},
                {'value': storage_base_number,"db_number": 262,'offset': 2,'value_type': 'int'},
                {'value': storage_pack_number,"db_number": 262,'offset': 4,'value_type': 'int'},
                {'value': storage_location_number,"db_number": 262,'offset': 10,'value_type': 'dint'},
                {'value': storage_pack_barcode,"db_number": 262,'offset': 14,"string_max_len": 18,'value_type': 'string'}
            ]
            for data in data_list:
                PlcClient().db_number_write(data)
        except Exception as e:
            _logger.error(f"库位信息写入失败！: {str(e)}")
            raise
    def stacker_information_write(self):
        """传递到PLC进行写入"""
        # 提取字段值
        stacker_goods_status = self. stacker_goods_status
        stacker_base_number = self. stacker_base_number
        stacker_pack_number = self. stacker_pack_number
        stacker_location_number = self. stacker_location_number
        stacker_pack_barcode = self. stacker_pack_barcode
        # plc_client = PlcClient()
        try:
            # 批量写入
            data_list = [
                {'value': stacker_goods_status, "db_number": 262, 'bit_index': 36, 'value_type': 'bool', },
                {'value': stacker_base_number, "db_number": 262, 'offset': 38, 'value_type': 'int'},
                {'value': stacker_pack_number, "db_number": 262, 'offset': 40, 'value_type': 'int'},
                {'value': stacker_location_number, "db_number": 262, 'offset': 46, 'value_type': 'dint'},
                {'value': stacker_pack_barcode, "db_number": 262, 'offset': 50, "string_max_len": 18,
                 'value_type': 'string'}
            ]
            for data in data_list:
                PlcClient().db_number_write(data)
        except Exception as e:
            _logger.error(f"库位信息写入失败！: {str(e)}")
            raise
    def entrance1_information_write(self):
        """传递到PLC进行写入"""
        # 提取字段值
        entrance1_goods_status = self.entrance1_goods_status
        entrance1_base_number = self.entrance1_base_number
        entrance1_pack_number = self.entrance1_pack_number
        entrance1_location_number = self.entrance1_location_number
        entrance1_pack_barcode = self.entrance1_pack_barcode
        # plc_client = PlcClient()
        try:
            # 批量写入
            data_list = [
                {'value': entrance1_goods_status, "db_number": 262, 'bit_index': 72, 'value_type': 'bool', },
                {'value': entrance1_base_number, "db_number": 262, 'offset': 74, 'value_type': 'int'},
                {'value': entrance1_pack_number, "db_number": 262, 'offset': 76, 'value_type': 'int'},
                {'value': entrance1_location_number, "db_number": 262, 'offset': 82, 'value_type': 'dint'},
                {'value': entrance1_pack_barcode, "db_number": 262, 'offset': 86, "string_max_len": 18,
                 'value_type': 'string'}
            ]
            for data in data_list:
                PlcClient().db_number_write(data)
        except Exception as e:
            _logger.error(f"库位信息写入失败！: {str(e)}")
            raise
    def entrance2_information_write(self):
        """传递到PLC进行写入"""
        # 提取字段值
        entrance2_goods_status = self.entrance2_goods_status
        entrance2_base_number = self.entrance2_base_number
        entrance2_pack_number = self.entrance2_pack_number
        entrance2_location_number = self.entrance2_location_number
        entrance2_pack_barcode = self.entrance2_pack_barcode
        # plc_client = PlcClient()
        try:
            # 批量写入
            data_list = [
                {'value': entrance2_goods_status, "db_number": 262, 'bit_index': 108, 'value_type': 'bool', },
                {'value': entrance2_base_number, "db_number": 262, 'offset': 110, 'value_type': 'int'},
                {'value': entrance2_pack_number, "db_number": 262, 'offset': 112, 'value_type': 'int'},
                {'value': entrance2_location_number, "db_number": 262, 'offset': 118, 'value_type': 'dint'},
                {'value': entrance2_pack_barcode, "db_number": 262, 'offset': 122, "string_max_len": 18,
                 'value_type': 'string'}
            ]
            for data in data_list:
                PlcClient().db_number_write(data)
        except Exception as e:
            _logger.error(f"库位信息写入失败！: {str(e)}")
            raise

    # @api.model
    def storage_information_read(self):
        """读取测试-批量"""
        results = [
            # 库位有货，序号，框号，库位号，框条码
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
            value = PlcClient().db_number_read(result)
            if num == 1:
                values_to_write['storage_goods_status'] = value
            elif num == 2:
                values_to_write['storage_base_number'] = value
            elif num == 3:
                values_to_write['storage_pack_number'] = value
            elif num == 4:
                values_to_write['storage_location_number'] = value
            elif num == 5:
                values_to_write['storage_pack_barcode'] = value
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
            value = PlcClient().db_number_read(result)
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
            value = PlcClient().db_number_read(result)
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
            value = PlcClient().db_number_read(result)
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
        record = self.browse(1)
        record.emergency_stop = not record.emergency_stop
        PlcClient().db_number_write(
            {'value': record.emergency_stop, "db_number": 260,'offset': 0,'bit_index': 5, 'value_type': 'bool', })

    def manual_auto_button(self):
        for record in self:
            record.manual_control = False
            record.auto_control = True

    def start_button(self):
        record = self.browse(1)
        record.start = not record.start
        PlcClient().db_number_write(
            {'value': record.start, "db_number": 260,'offset': 0,'bit_index': 0, 'value_type': 'bool', })

    def stop_button(self):
        record = self.browse(1)
        record.stop = not record.stop
        PlcClient().db_number_write(
            {'value': record.stop, "db_number": 260,'offset': 0,'bit_index': 1, 'value_type': 'bool', })

    def pause_button(self):
        record = self.browse(1)
        record.pause = not record.pause
        PlcClient().db_number_write(
            {'value': record.pause, "db_number": 260,'offset': 0,'bit_index': 2, 'value_type': 'bool', })

    def reset_button(self):
        record = self.browse(1)
        record.reset = not record.reset
        PlcClient().db_number_write(
            {'value': record.reset, "db_number": 260,'offset': 0,'bit_index': 3, 'value_type': 'bool', })

    def store_button(self):
        record = self.browse(1)
        record.store = not record.store
        record.outbound =  False
        record.return_store =  False
        PlcClient().db_number_write(
            {'value': record.store, "db_number": 260,'offset': 2,'bit_index': 0,'value_type': 'bool', })
        PlcClient().db_number_write(
            {'value': False, "db_number": 260,'offset': 2,'bit_index': 1, 'value_type': 'bool', })
        PlcClient().db_number_write(
            {'value': False, "db_number": 260,'offset': 2, 'bit_index': 2, 'value_type': 'bool', })
    def outbound_button(self):
        record = self.browse(1)
        record.store = False
        record.outbound = not record.outbound
        record.return_store = False
        PlcClient().db_number_write(
            {'value': False, "db_number": 260,'offset': 2,'bit_index': 0,'value_type': 'bool', })
        PlcClient().db_number_write(
            {'value': record.outbound, "db_number": 260, 'offset': 2, 'bit_index': 1, 'value_type': 'bool', })
        PlcClient().db_number_write(
            {'value': False, "db_number": 260, 'offset': 2, 'bit_index': 2, 'value_type': 'bool', })
    def return_store_button(self):
        record = self.browse(1)
        record.store =  False
        record.outbound =  False
        record.return_store = not record.return_store
        PlcClient().db_number_write(
            {'value': False, "db_number": 260, 'offset': 2, 'bit_index': 0, 'value_type': 'bool', })
        PlcClient().db_number_write(
            {'value': False, "db_number": 260, 'offset': 2, 'bit_index': 1, 'value_type': 'bool', })
        PlcClient().db_number_write(
            {'value': record.return_store, "db_number": 260, 'offset': 2, 'bit_index': 2, 'value_type': 'bool', })



















































