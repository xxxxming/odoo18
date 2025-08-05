# -*- coding: utf-8 -*-
import logging
from email.policy import default

from reportlab.lib.pagesizes import elevenSeventeen

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
    move_stock = fields.Boolean(string="移库")
    store = fields.Boolean(string="入库")
    outbound = fields.Boolean(string="出库")
    return_store = fields.Boolean(string="返库")
    allow_move_stock = fields.Boolean(string="允许移库")
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
        ('start', '开始'),
        ('reach_source_target', '到源目标'),
        ('take_finish', '取料完成'),
        ('reach_new_target', '到新目标'),
        ('feed_finish', '送料完成'),
        ('finish', '任务完成'),
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

    # 添加日志相关字段
    log_messages = fields.Text(string='Operation Logs', readonly=True)
    # first_40_logs = fields.Text(string='First 40 Logs', compute='_compute_first_40_logs', readonly=True)
    # last_40_logs = fields.Text(string='Last 40 Logs', compute='_compute_last_40_logs', readonly=True)
    first_30_logs = fields.Text(string='First 30 Logs', readonly=True)
    last_30_logs = fields.Text(string='Last 30 Logs', readonly=True)

    @api.depends('storage_goods_status')
    def _compute_one_second(self):
        pass

    @api.onchange('entrance')
    def _onchange_entrance(self):
        print('entrance change!')
        record = self.browse(1)
        if record.exists():
            self.compare_pack_number()
            self.command_data_write()

    @api.onchange('pack_number')
    def _onchange_pack_number(self):
        print('pack change!')
        # record = self.browse(1)
        record = self.browse(1)
        if record.exists():
            record.write({'pack_number': self.pack_number})
            self.compare_pack_number()
            self.command_data_write()
            self.refresh_fields_turn_on()

    @api.onchange('pack_barcode')
    def _onchange_barcode(self):
        print('barcode change!')
        self.compare_pack_barcode()
    def compare_pack_barcode(self):
        barcode_record = self.env['warehouse.frame.barcode'].search(
            [('frame_barcode', '=', self.pack_barcode)], limit=1)

        if barcode_record:
            self.pack_number = barcode_record.frame_number
            print('Find barcode!')
            record = self.browse(1)
            print(record)
            record.write({
                'pack_number': barcode_record.frame_number,
            })
            self.compare_pack_number()
            self.refresh_fields_turn_on()
        else:
            raise UserError("未找到条码，请确认是否正确。如果是新条码，请从新登记。")

    def compare_pack_number(self):

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
                'allow_move_stock': False,
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
                storage_record.write({
                    'pack_barcode': barcode_record.frame_barcode,
                })
            # 如果能在库存里找到对应的框号，则获取库位信息
            if storage_record:
                record.write({
                    'pack_number': storage_record.pack_number,
                    'location_number': storage_record.location_number,
                })
                if storage_record.goods_status == True:

                    if self.entrance:
                        record.write({
                            'source_target': storage_record.location_number,
                        })
                        record.write({
                            'allow_move_stock': False,
                            'allow_store': False,
                            'allow_outbound': True,
                            'allow_return': False,
                        })
                        if self.entrance == 'entrance1':
                            record.write({
                            'new_target': entrance_1,
                            })
                        if self.entrance == 'entrance2':
                            record.write({
                            'new_target': entrance_2,
                            })
                    else:
                        record.write({
                            'allow_move_stock': True,
                            'allow_store': False,
                            'allow_outbound': False,
                            'allow_return': False,
                        })
                        record.write({
                            'source_target': storage_record.location_number,
                        })
                        self.find_empty_location()
                        record.write({
                            'new_target': record.location_number,
                        })
                else:
                    record.write({
                        'allow_move_stock': False,
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
                    'allow_move_stock': False,
                    'allow_store': True,
                    'allow_outbound': False,
                    'allow_return': False,
                })
                self.find_empty_location()
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

    def find_empty_location(self):
        record = self.browse(1)
        record_settings = self.env['warehouse.settings'].search([], limit=1)
        entrance_1 = record_settings.entrance_1
        entrance_2 = record_settings.entrance_2
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

        if column_layer_1 < column_layer_2:
            record.write({
                'location_number': location_record_1.location_number,
            })
        else:
            record.write({
                'location_number': location_record_2.location_number,
            })

    def command_data_write(self):
        record = self.browse(1)
        entrance = 0
        allow_move_stock = record.allow_move_stock
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
                {'value': allow_move_stock, "db_number": 260, 'offset': 2, 'bit_index': 4, 'value_type': 'bool'},
                {'value': allow_store, "db_number": 260, 'offset': 2, 'bit_index': 5, 'value_type': 'bool'},
                {'value': allow_outbound, "db_number": 260, 'offset': 2, 'bit_index': 6, 'value_type': 'bool'},
                {'value': allow_return, "db_number": 260, 'offset': 2, 'bit_index': 7, 'value_type': 'bool'},
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
            self.refresh_fields_turn_off()

    def storage_information_write(self):
        """传递到PLC进行写入"""
        # 提取字段值
        storage_goods_status = self.storage_goods_status
        storage_base_number = self.storage_base_number
        storage_pack_number = self.storage_pack_number
        storage_location_number = self.storage_location_number
        storage_pack_barcode = self.storage_pack_barcode

        try:
            # 批量写入
            data_list = [
                {'value': storage_goods_status,"db_number": 262,'offset': 0,'bit_index': 0,'value_type': 'bool'},
                {'value': storage_base_number,"db_number": 262,'offset': 2,'value_type': 'int'},
                {'value': storage_pack_number,"db_number": 262,'offset': 4,'value_type': 'int'},
                {'value': storage_location_number,"db_number": 262,'offset': 6,'value_type': 'dint'},
                {'value': storage_pack_barcode,"db_number": 262,'offset': 10,"string_max_len": 18,'value_type': 'string'}
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
                {'value': stacker_goods_status, "db_number": 262, 'bit_index': 32, 'value_type': 'bool', },
                {'value': stacker_base_number, "db_number": 262, 'offset': 34, 'value_type': 'int'},
                {'value': stacker_pack_number, "db_number": 262, 'offset': 36, 'value_type': 'int'},
                {'value': stacker_location_number, "db_number": 262, 'offset': 38, 'value_type': 'dint'},
                {'value': stacker_pack_barcode, "db_number": 262, 'offset': 42, "string_max_len": 18,
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
                {'value': entrance1_goods_status, "db_number": 262, 'bit_index': 64, 'value_type': 'bool', },
                {'value': entrance1_base_number, "db_number": 262, 'offset': 66, 'value_type': 'int'},
                {'value': entrance1_pack_number, "db_number": 262, 'offset': 68, 'value_type': 'int'},
                {'value': entrance1_location_number, "db_number": 262, 'offset': 70, 'value_type': 'dint'},
                {'value': entrance1_pack_barcode, "db_number": 262, 'offset': 74, "string_max_len": 18,
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
                {'value': entrance2_goods_status, "db_number": 262, 'bit_index': 96, 'value_type': 'bool', },
                {'value': entrance2_base_number, "db_number": 262, 'offset': 98, 'value_type': 'int'},
                {'value': entrance2_pack_number, "db_number": 262, 'offset': 100, 'value_type': 'int'},
                {'value': entrance2_location_number, "db_number": 262, 'offset': 102, 'value_type': 'dint'},
                {'value': entrance2_pack_barcode, "db_number": 262, 'offset': 106, "string_max_len": 18,
                 'value_type': 'string'}
            ]
            for data in data_list:
                PlcClient().db_number_write(data)
        except Exception as e:
            _logger.error(f"库位信息写入失败！: {str(e)}")
            raise
    def storage_information_read(self):
        """读取测试-批量"""
        results = [
            # 库位有货，序号，框号，库位号，框条码
            {'db_number': 262, 'offset': 0, 'value_type': 'bool', 'bit_index': 0},
            {'db_number': 262, 'offset': 2, 'value_type': 'int'},
            {'db_number': 262, 'offset': 4, 'value_type': 'int'},
            {'db_number': 262, 'offset': 6, 'value_type': 'dint'},
            {'db_number': 262, 'offset': 10, 'value_type': 'string', "string_max_len": 18},
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
            # record = self.env['warehouse.system.operate'].browse(1)
            record.write(values_to_write)
    def stacker_information_read(self):
        """读取测试-批量"""
        results = [
            #库位有货，框号，库位号，框条码
            {'db_number': 262, 'offset': 32, 'value_type': 'bool', 'bit_index':0},
            {'db_number': 262, 'offset': 34, 'value_type': 'int'},
            {'db_number': 262, 'offset': 36, 'value_type': 'int'},
            {'db_number': 262, 'offset': 38, 'value_type': 'dint'},
            {'db_number': 262, 'offset': 42, 'value_type': 'string', "string_max_len": 18},
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
            {'db_number': 262, 'offset': 64, 'value_type': 'bool', 'bit_index':0},
            {'db_number': 262, 'offset': 66, 'value_type': 'int'},
            {'db_number': 262, 'offset': 68, 'value_type': 'int'},
            {'db_number': 262, 'offset': 70, 'value_type': 'dint'},
            {'db_number': 262, 'offset': 74, 'value_type': 'string', "string_max_len": 18},
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
            {'db_number': 262, 'offset': 96, 'value_type': 'bool', 'bit_index':0},
            {'db_number': 262, 'offset': 98, 'value_type': 'int'},
            {'db_number': 262, 'offset': 100, 'value_type': 'int'},
            {'db_number': 262, 'offset': 102, 'value_type': 'dint'},
            {'db_number': 262, 'offset': 106, 'value_type': 'string', "string_max_len": 18},
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

    def move_stock_button(self):
        self.target_data_check()
        record = self.browse(1)
        if record.allow_move_stock:
            record.move_stock = not record.move_stock
            record.store = False
            record.outbound =  False
            record.return_store =  False
            log_message = f"执行移库命令:库位{record.source_target} 移到库位{record.new_target} ！"
            _logger.info(log_message)
            record.log_operation(log_message)
        else:
            raise UserError("不允许执行移库命令！")

    def store_button(self):
        self.target_data_check()
        record = self.browse(1)
        if record.allow_store:
            record.move_stock = False
            record.store = not record.store
            record.outbound =  False
            record.return_store =  False
            self.command_button_write()
            log_message = f"执行入库命令:库位{record.source_target} 移到库位{record.new_target} ！"
            _logger.info(log_message)
            record.log_operation(log_message)
        else:
            raise UserError(f"不允许执行入库命令！")

    def outbound_button(self):
        self.target_data_check()
        record = self.browse(1)
        if record.allow_outbound:
            record.move_stock = False
            record.store = False
            record.outbound = not record.outbound
            record.return_store = False
            self.command_button_write()
            log_message = f"执行出库命令:库位{record.source_target} 移到{record.entrance}：{record.new_target} ！"
            _logger.info(log_message)
            record.log_operation(log_message)
        else:
            raise UserError(f"不允许执行出库命令！")
    def return_store_button(self):
        self.target_data_check()
        record = self.browse(1)
        if record.allow_return:
            record.move_stock = False
            record.store =  False
            record.outbound =  False
            record.return_store = not record.return_store
            self.command_button_write()
            log_message = f"执行返库命令:库位{record.source_target} 移到库位{record.new_target} ！"
            _logger.info(log_message)
            record.log_operation(log_message)
        else:
            raise UserError(f"不允许执行返库命令！")

    def command_button_write(self):
        record = self.browse(1)
        if not record.emergency_stop:
            try:
                # 批量写入
                data_list = [
                    {'value': record.move_stock, "db_number": 260,'offset': 2,'bit_index': 0,'value_type': 'bool'},
                    {'value': record.store, "db_number": 260,'offset': 2,'bit_index': 1,'value_type': 'bool'},
                    {'value': record.outbound, "db_number": 260,'offset': 2,'bit_index': 2,'value_type': 'bool'},
                    {'value': record.return_store, "db_number": 260,'offset': 2,'bit_index': 3,'value_type': 'bool'}
                ]
                for data in data_list:
                    PlcClient().db_number_write(data)
            except Exception as e:
                _logger.error(f"仓库命令信息写入失败！: {str(e)}")
                raise

    def target_data_check(self):
        record = self.browse(1)
        source_target = record.source_target
        new_target = record.new_target
        source_building = source_target // 10000  # 取前两位
        source_remaining = source_target % 10000  # 剩余部分为后四位
        source_column = source_remaining // 100  # 取中间两位
        source_layer = source_remaining % 100  # 取最后两位

        new_building = new_target // 10000  # 取前两位
        new_remaining = new_target % 10000  # 剩余部分为后四位
        new_column = new_remaining // 100  # 取中间两位
        new_layer = new_remaining % 100  # 取最后两位

        settings = self.env['warehouse.settings'].search([], limit=1)
        if not settings:
           _logger.error("未找到参数，请先设置基本参数!")
           raise UserError("未找到参数，请先设置基本参数!")
        if source_building < 1:
            raise UserError(f"源目标栋参数 {source_building} 小于 1 ！")
        if source_building > settings.building:
            raise UserError(f"源目标栋参数 {source_building} 大于最大允许值 {settings.building} ！")
        if source_column < 1:
            raise UserError(f"源目标列参数 {source_column} 小于 1 ！")
        if source_column > settings.column:
            raise UserError(f"源列目标列参数 {source_column} 大于最大允许值 {settings.column} ！")
        if source_layer < 1:
            raise UserError(f"源目标层参数 {source_layer} 小于 1 ！")
        if source_layer > settings.column:
            raise UserError(f"源目标层参数 {source_layer} 大于最大允许值 {settings.layer} ！")

        if new_building < 1:
            raise UserError(f"新目标栋参数 {new_building} 小于 1 ！")
        if new_building > settings.building:
            raise UserError(f"新目标栋参数 {new_building} 大于最大允许值 {settings.building} ！")
        if new_column < 1:
            raise UserError(f"新目标列参数 {new_column} 小于 1 ！")
        if new_column > settings.column:
            raise UserError(f"新列目标列参数 {new_column} 大于最大允许值 {settings.column} ！")
        if new_layer < 1:
            raise UserError(f"新目标层参数 {new_layer} 小于 1 ！")
        if new_layer > settings.column:
            raise UserError(f"新目标层参数 {source_layer} 大于最大允许值 {settings.layer} ！")

    def clear_logs(self):
        """清除日志"""
        self.log_messages = ""
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def refresh_fields_turn_on(self):
        record = self.browse(1)
        record.refresh_status = True
    def refresh_fields_turn_off(self):
        record = self.browse(1)
        record.refresh_status = False

    # def log_operation(self, message):
    #     """记录操作日志"""
    #     current_logs = self.log_messages or ""
    #     timestamp = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #     new_log = f"[{timestamp}] {message}\n"
    #     self.log_messages = new_log + current_logs

    def log_operation(self, message):
        """记录操作日志，限制总记录数为100条以保持性能"""
        current_logs = self.log_messages or ""
        # 使用用户时区获取时间戳，解决时区不一致问题
        user_tz = self.env.user.tz or 'UTC'
        timestamp = fields.Datetime.context_timestamp(self.env.user, fields.Datetime.now()).strftime(
            "%Y-%m-%d %H:%M:%S")
        new_log = f"[{timestamp}] {message}\n"

        # 将现有日志按行分割
        log_lines = current_logs.splitlines()
        # 添加新日志到最前面
        log_lines.insert(0, f"[{timestamp}] {message}")
        # 只保留最新的100条记录以保持性能
        log_lines = log_lines[:100]
        # 重新组合日志
        self.log_messages = "\n".join(log_lines) + "\n"
        self.load_first_30_logs()
        self.load_last_30_logs()

    def load_first_30_logs(self):
        """计算并显示前35条日志记录"""
        for record in self:
            if record.log_messages:
                log_lines = record.log_messages.splitlines()
                # 获取前35条记录
                first_lines = log_lines[:30]
                # record.first_40_logs = "\n".join(first_lines)
                # 为每行添加序号
                numbered_lines = [f"{i + 1:2d}. {line}" for i, line in enumerate(first_lines)]
                record.first_30_logs = "\n".join(numbered_lines)
            else:
                record.first_30_logs = ""

    def load_last_30_logs(self):
        """计算并显示后35条日志记录"""
        for record in self:
            if record.log_messages:
                log_lines = record.log_messages.splitlines()
                # 只有当总记录数大于30条时才显示后30条记录
                if len(log_lines) > 30:
                    if len(log_lines) > 60:
                        middle_lines = log_lines[30:60]
                        numbered_lines = [f"{i + 31:2d}. {line}" for i, line in enumerate(middle_lines)]
                        record.last_30_logs = "\n".join(numbered_lines)
                    else:
                        # 如果总记录数在31到60之间，显示从第31条到末尾的记录
                        middle_lines = log_lines[30:]
                    # record.last_40_logs = "\n".join(middle_lines)
                        # 为每行添加序号
                        numbered_lines = [f"{i + 31:2d}. {line}" for i, line in enumerate(middle_lines)]
                        record.last_30_logs = "\n".join(numbered_lines)
                else:
                    # 如果总记录数不超过30条，则不显示任何内容
                    record.last_30_logs = ""
            else:
                record.last_30_logs = ""