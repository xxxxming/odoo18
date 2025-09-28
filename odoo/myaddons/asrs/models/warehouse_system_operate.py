# -*- coding: utf-8 -*-
import logging
import threading
import time
from email.policy import default

from reportlab.lib.pagesizes import elevenSeventeen

import odoo
from odoo import models, fields, api, SUPERUSER_ID
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
# 添加互斥锁相关变量
method_lock = threading.Lock()
last_method_execution_time = 0
lock_timeout = 3  # 锁超时时间（秒）


# class AutomaticStorageLocation(models.Model):
#
#     _name = 'automatic.storage.location'
#     _description = 'automatic storage location'
#
#
#     goods_status = fields.Boolean(string='库位有货')
#     goods_cancel = fields.Boolean(string='取消库位')
#     fixed_pack_number = fields.Boolean(string='绑定框号')
#     fixed_pack_barcode = fields.Boolean(string='绑定条码')
#     pack_number = fields.Integer(string='框号')
#     base_number = fields.Integer(string='库位编号')
#     location_number = fields.Integer(string='库位号')
#     pack_barcode = fields.Char(string='框条码')

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
    load_data = fields.Boolean(string="加载数据")
    pack_number = fields.Integer(string='输入框号')
    base_number = fields.Integer(string='输入序号')
    pack_number_old = fields.Integer(string='上次框号')
    location_number = fields.Integer(string='库位号')
    empty_location = fields.Integer(string="空库位")
    pack_number_find_code = fields.Char(string="框号查代码")
    pack_barcode = fields.Char(string='框条码')
    source_target = fields.Integer(string="源目标")
    new_target = fields.Integer(string="新目标")
    entrance = fields.Selection(string='选择出入口',
    selection=[('entrance1', '出入口1'), ('entrance2', '出入口2')])
    status = fields.Selection([
        ('start', '开始'),
        ('reach_source_target', '到源目标'),
        ('take_finish', '取料完成'),
        ('reach_new_target', '到新目标'),
        ('feed_finish', '送料完成'),
        ('finish', '任务完成'),
        ('idle', '空闲')
    ], string="状态", default='idle')
    netcontrol = fields.Boolean(string='网络控制')
    netdata = fields.Boolean(string='网络数据')
    auto_ready = fields.Boolean(string='自动就绪')

    current_user_id = fields.Many2one('res.users', '当前用户', compute='_compute_current_user')
    current_user_name = fields.Char('操作员', compute='_compute_current_user')
    Operation_permissions = fields.Boolean(string='操作权限')

    # 存储区字段 (Storage fields)
    storage_goods_status = fields.Boolean(string='库位有货')
    storage_goods_cancel = fields.Boolean(string='取消库位')
    storage_fixed_pack_number = fields.Boolean(string='绑定框号',store=True)
    storage_fixed_pack_barcode = fields.Boolean(string='绑定条码',store=True)
    storage_pack_number = fields.Integer(string='框号',store=True)
    storage_base_number = fields.Integer(string='序号',store=True)
    storage_location_number = fields.Integer(string='库位号',store=True)
    storage_pack_barcode = fields.Char(string='框条码',store=True)

    # 堆垛机字段 (Stacker fields)
    stacker_goods_status = fields.Boolean(string='库位有货')
    stacker_goods_cancel = fields.Boolean(string='取消库位')
    stacker_fixed_pack_number = fields.Boolean(string='绑定框号')
    stacker_fixed_pack_barcode = fields.Boolean(string='绑定条码')
    stacker_pack_number = fields.Integer(string='框号')
    stacker_base_number = fields.Integer(string='序号')
    stacker_location_number = fields.Integer(string='库位号')
    stacker_pack_barcode = fields.Char(string='框条码')

    # 入口1字段 (Entrance 1 fields)
    entrance1_goods_status = fields.Boolean(string='库位有货')
    entrance1_goods_cancel = fields.Boolean(string='取消库位')
    entrance1_fixed_pack_number = fields.Boolean(string='绑定框号')
    entrance1_fixed_pack_barcode = fields.Boolean(string='绑定条码')
    entrance1_pack_number = fields.Integer(string='框号')
    entrance1_base_number = fields.Integer(string='序号')
    entrance1_location_number = fields.Integer(string='库位号')
    entrance1_pack_barcode = fields.Char(string='框条码')

    # 入口2字段 (Entrance 2 fields)
    entrance2_goods_status = fields.Boolean(string='库位有货')
    entrance2_goods_cancel = fields.Boolean(string='取消库位')
    entrance2_fixed_pack_number = fields.Boolean(string='绑定框号')
    entrance2_fixed_pack_barcode = fields.Boolean(string='绑定条码')
    entrance2_pack_number = fields.Integer(string='框号')
    entrance2_base_number = fields.Integer(string='序号')
    entrance2_location_number = fields.Integer(string='库位号')
    entrance2_pack_barcode = fields.Char(string='框条码')

    # 入口2字段 (Entrance 2 fields)
    move_store_goods_status = fields.Boolean(string='库位有货')
    move_store_goods_cancel = fields.Boolean(string='取消库位')
    move_store_fixed_pack_number = fields.Boolean(string='绑定框号')
    move_store_fixed_pack_barcode = fields.Boolean(string='绑定条码')
    move_store_pack_number = fields.Integer(string='框号')
    move_store_base_number = fields.Integer(string='序号')
    move_store_location_number = fields.Integer(string='库位号')
    move_store_pack_barcode = fields.Char(string='框条码')

    x_dummy_widget_field = fields.Char(string='Dummy Widget Field')
    refresh_status = fields.Boolean(string='是否自动刷新')
    status_code = fields.Boolean(string='状态码')

    # 添加日志相关字段
    log_messages = fields.Text(string='Operation Logs', readonly=True)
    # first_40_logs = fields.Text(string='First 40 Logs', compute='_compute_first_40_logs', readonly=True)
    # last_40_logs = fields.Text(string='Last 40 Logs', compute='_compute_last_40_logs', readonly=True)
    first_30_logs = fields.Text(string='First 30 Logs', readonly=True)
    last_30_logs = fields.Text(string='Last 30 Logs', readonly=True)




    @api.depends('storage_goods_status')
    def _compute_one_second(self):
        pass

    @api.depends()
    def _compute_current_user(self):
        for record in self:
            record.current_user_id = self.env.user.id
            record.current_user_name = self.env.user.name
            if  record.current_user_name == 'admin':
                record.write({'Operation_permissions': True})
            elif  record.current_user_name == 'hugo':
                record.write({'Operation_permissions': True})
            elif  record.current_user_name == '劳汝清':
                record.write({'Operation_permissions': True})
            elif  record.current_user_name == '邓志光':
                record.write({'Operation_permissions': True})
            else:
                record.write({'Operation_permissions': False})


    @api.onchange('entrance')
    def _onchange_entrance(self):
        # 尝试获取锁，如果获取不到直接返回
        global last_method_execution_time
        if not method_lock.acquire(timeout=0):
            return
        try:
            current_time = time.time()
            # 检查是否在锁定时间内
            if current_time - last_method_execution_time < lock_timeout:
                return
            control_system = self.env['warehouse.control.system'].search([], limit=1)
            task_running = control_system.task_running
            if task_running:
                raise UserError("任务执行中，不允许更改！")
            else:
                record = self.browse(1)
                if record.exists():
                    self.compare_pack_number()
                    # self.command_status_reset()
                    self.command_data_write(2)

            # 更新最后执行时间
            last_method_execution_time = time.time()
        finally:
            # 释放锁
            method_lock.release()

    @api.onchange('pack_number')
    def _onchange_pack_number(self):
        global last_method_execution_time
        # 尝试获取锁，如果获取不到直接返回
        if not method_lock.acquire(timeout=0):
            return
        try:
            current_time = time.time()
            # 检查是否在锁定时间内
            if current_time - last_method_execution_time < lock_timeout:
                return
            control_system = self.env['warehouse.control.system'].search([], limit=1)
            task_running = control_system.task_running
            if task_running:
                raise UserError("任务执行中，不允许更改！")
            else:
                record = self.browse(1)
                if self.pack_number == 0:
                    self.write({'pack_number': record.pack_number_old})
                else:
                    record.write({'pack_number': self.pack_number,
                                  'pack_number_old': self.pack_number})
                    self.compare_pack_number()
                    self.command_data_write(2)
                    # self.refresh_fields_turn_on()

                    self.reset_pc_command()
            # 更新最后执行时间
            last_method_execution_time = time.time()
        finally:
            # 释放锁
            method_lock.release()
    @api.onchange('pack_barcode')
    def _onchange_barcode(self):
        global last_method_execution_time
        # 尝试获取锁，如果获取不到直接返回
        if not method_lock.acquire(timeout=0):
            return
        try:
            current_time = time.time()
            # 检查是否在锁定时间内
            if current_time - last_method_execution_time < lock_timeout:
                return
            control_system = self.env['warehouse.control.system'].search([], limit=1)
            task_running = control_system.task_running
            if task_running:
                raise UserError("任务执行中，不允许更改！")
            else:
                self.compare_pack_barcode()
            # 更新最后执行时间
            last_method_execution_time = time.time()
        finally:
            # 释放锁
            method_lock.release()
    def compare_pack_barcode(self):
        barcode_record = self.env['warehouse.frame.barcode'].search(
            [('frame_barcode', '=', self.pack_barcode)], limit=1)

        if barcode_record:
            self.pack_number = barcode_record.frame_number
            record = self.browse(1)
            record.write({
                'pack_number': barcode_record.frame_number,
            })
            self.compare_pack_number()

            # self.refresh_fields_turn_on()
        else:
            raise UserError("未找到条码，请确认是否正确。如果是新条码，请从新登记。")

    def compare_pack_number(self):

        if self.pack_number != 0:
            # 一次性获取所有需要的设置和记录信息
            record_settings = self.env['warehouse.settings'].search([], limit=1)
            entrance_1 = record_settings.entrance_1
            entrance_2 = record_settings.entrance_2

            record = self.browse(1)
            # 同时查询库存记录和条码记录
            storage_record = self.env['warehouse.location.information'].search(
                [('pack_number', '=', self.pack_number)], limit=1)
            barcode_record = self.env['warehouse.frame.barcode'].search(
                [('frame_number', '=', self.pack_number)],
                limit=1)
                # if not storage_record or not storage_record.pack_barcode else None

            # 检查barcode_record是否存在，避免访问None对象属性
            if barcode_record:
                record.pack_number_find_code = barcode_record.frame_barcode

            else:
                record.pack_number_find_code = 'No found!'

            # 保存变更前的值用于比较
            old_values = {
                'allow_move_stock': record.allow_move_stock,
                'allow_store': record.allow_store,
                'allow_outbound': record.allow_outbound,
                'allow_return': record.allow_return,
                'pack_barcode': record.pack_barcode,
                'pack_number': record.pack_number,
                'location_number': record.location_number,
                'source_target': record.source_target,
                'new_target': record.new_target,
                # 'empty_location': record.empty_location,
            }

            # 初始化默认值
            vals = {
                'allow_move_stock': False,
                'allow_store': False,
                'allow_outbound': False,
                'allow_return': False,
            }
            # 查找空库位
            self.find_empty_location()

            # 如果库存中数据中没有对应的框条码，则获取框条码
            if storage_record and storage_record.pack_barcode:
                vals['pack_barcode'] = storage_record.pack_barcode
            elif barcode_record and barcode_record.frame_barcode:
                vals['pack_barcode'] = barcode_record.frame_barcode
                if storage_record:
                    storage_record.write({
                        'pack_barcode': barcode_record.frame_barcode,
                    })
            else:
                vals['pack_barcode'] = 'No found!'
                # storage_record.write({
                #     'pack_barcode': 'No found!'
                # })

            # 如果能在库存里找到对应的框号，则获取库位信息
            if storage_record:

                vals.update({
                    'pack_number': storage_record.pack_number,
                    'location_number': storage_record.location_number,
                })

                if storage_record.goods_status:

                    if self.entrance:
                        vals['source_target'] = storage_record.location_number
                        vals.update({
                            'allow_move_stock': False,
                            'allow_store': False,
                            'allow_outbound': True,
                            'allow_return': False,
                        })
                        if self.entrance == 'entrance1':
                            vals['new_target'] = entrance_1
                        elif self.entrance == 'entrance2':
                            vals['new_target'] = entrance_2
                    else:
                        vals.update({
                            'allow_move_stock': True,
                            'allow_store': False,
                            'allow_outbound': False,
                            'allow_return': False,
                            'source_target': storage_record.location_number,
                        })
                        # self.find_empty_location()
                        # vals['new_target'] = record.location_number
                        # 执行移库，使用空库位
                        vals['new_target'] = record.empty_location
                else:
                    vals.update({
                        'allow_move_stock': False,
                        'allow_store': False,
                        'allow_outbound': False,
                        'allow_return': True,
                    })
                    if not self.entrance or self.entrance == 'entrance1':
                        vals['source_target'] = entrance_1
                    elif self.entrance == 'entrance2':
                        vals['source_target'] = entrance_2
                    vals['new_target'] = storage_record.location_number
            else:

                vals.update({
                    'allow_move_stock': False,
                    'allow_store': True,
                    'allow_outbound': False,
                    'allow_return': False,
                })
                vals['new_target'] = record.empty_location

                if  not barcode_record.frame_barcode and not storage_record.pack_barcode:
                    vals.update({
                        'allow_move_stock': False,
                        'allow_store': False,
                        'allow_outbound': False,
                        'allow_return': False,
                    })
                    vals['pack_barcode'] = 'No found!'
                    vals['location_number'] = 0
                    vals['new_target'] = record.empty_location


                # 入库选择默认出入口1或者按选择出入口
                if not self.entrance or self.entrance == 'entrance1':
                    vals['source_target'] = entrance_1
                elif self.entrance == 'entrance2':
                    vals['source_target'] = entrance_2

            # if record.empty_location!=0:
            # vals['empty_location'] = record.empty_location

            # 一次性写入所有值
            record.write(vals)

            # 检查哪些字段发生了变化
            changed_fields = {}
            for field, new_value in vals.items():
                if field in old_values and old_values[field] != new_value:
                    changed_fields[field] = new_value

            # 如果有字段发生变化，则发送通知到频道
            if changed_fields:
                # 确保数值字段类型正确
                typed_changed_fields = {}
                for field, value in changed_fields.items():
                    if field in ['pack_number', 'location_number', 'source_target', 'new_target', 'base_number']:
                        # 确保这些字段是整数类型
                        try:
                            typed_changed_fields[field] = int(value) if value is not None else 0
                        except (ValueError, TypeError):
                            typed_changed_fields[field] = 0
                    elif field in ['allow_move_stock', 'allow_store', 'allow_outbound', 'allow_return']:
                        # 确保这些字段是布尔类型
                        typed_changed_fields[field] = bool(value) if value is not None else False
                    elif field in ['pack_barcode']:
                        # 确保这些字段是字符串类型
                        typed_changed_fields[field] = str(value) if value is not None else ""
                    else:
                        # 其他字段保持原样
                        typed_changed_fields[field] = value if value is not None else ""

                # 发送通知到bus频道，添加错误处理
                try:
                    self.env['bus.bus']._sendone(
                        channel_with_db(self.env.cr.dbname, 'warehouse_data_update'),
                        'warehouse.data_update',
                        {
                            'model': 'warehouse.system.operate',
                            'id': record.id,
                            'changed_fields': typed_changed_fields
                        }
                    )
                    _logger.info(f"Sent bus {typed_changed_fields} with ID {record.id}")
                except Exception as e:
                    _logger.warning(f"Failed to send bus notification: {str(e)}")

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
             ('goods_status', '=', False)], limit=5)
        location_record_2 = self.env['warehouse.location.information'].search(
            [('location_number', '!=', entrance_1),
             ('location_number', '!=', entrance_2),
             ('location_number', '>', 20000),
             ('goods_cancel', '=', False),
             ('goods_status', '=', False)], limit=5)

        # for record in location_record_1:
        #     print('B1', record.location_number)
        # for record in location_record_2:
        #     print('B2', record.location_number)

        if location_record_1 and not location_record_2:
            record.write({
                'empty_location': location_record_1[0].location_number,
            })

        if not location_record_1 and location_record_2:
            record.write({
                'empty_location': location_record_2[0].location_number,
            })

        if location_record_1 and location_record_2:
            column_layer_1 = location_record_1[0].location_number % 10000
            column_layer_2 = location_record_2[0].location_number % 10000
            if column_layer_1 < column_layer_2:
                record.write({
                    'empty_location': location_record_1[0].location_number,
                })
            else:
                record.write({
                    'empty_location': location_record_2[0].location_number,
                })

        if not location_record_1 and not location_record_2:
            record.write({
                'empty_location': 0,
            })
            _logger.warning("No empty location found.")

    def command_data_write(self,address):
        information_record = self.env['warehouse.location.information'].search(
            [('pack_number', '=', self.pack_number)], limit=1)
        record = self.browse(1)

        entrance = 0
        allow_move_stock = record.allow_move_stock
        allow_store = record.allow_store
        allow_outbound = record.allow_outbound
        allow_return = record.allow_return

        load_data = True
        pack_number = record.pack_number
        # base_number = record.base_number
        base_number = information_record.base_number
        source_target = record.source_target
        new_target = record.new_target
        location_number = record.location_number
        empty_location = record.empty_location
        pack_number_find_code = record.pack_number_find_code
        pack_barcode = record.pack_barcode

        if information_record.pack_barcode:
            info_goods = information_record.goods_status
            info_cancel = information_record.goods_cancel
            info_fixed_pack_number = information_record.fixed_pack_number
            info_fixed_pack_barcode = information_record.fixed_pack_barcode
            info_base_number = information_record.base_number
            info_pack_number = information_record.pack_number
            info_location_number = information_record.location_number
            info_pack_barcode = information_record.pack_barcode
        else:
            info_goods = False
            info_cancel = False
            info_fixed_pack_number = False
            info_fixed_pack_barcode = False
            info_base_number = 0
            info_pack_number = 0
            info_location_number = 0
            info_pack_barcode = 'No found!'

        if self.entrance == False:
            entrance = 0
        if self.entrance == 'entrance1':
            entrance = 1
        if self.entrance == 'entrance2':
            entrance = 2
        # plc_client = PlcClient()

        try:
            # 批量写入
            data_list = [
                {'value': allow_move_stock, "db_number": 260, 'offset': address, 'bit_index': 4, 'value_type': 'bool'},
                {'value': allow_store, "db_number": 260, 'offset': address, 'bit_index': 5, 'value_type': 'bool'},
                {'value': allow_outbound, "db_number": 260, 'offset': address, 'bit_index': 6, 'value_type': 'bool'},
                {'value': allow_return, "db_number": 260, 'offset': address, 'bit_index': 7, 'value_type': 'bool'},
                {'value': load_data, "db_number": 260, 'offset': address + 1, 'bit_index': 0, 'value_type': 'bool'},
                {'value': entrance,"db_number": 260,'offset': address+2,'value_type': 'int'},
                {'value': pack_number,"db_number": 260,'offset': address+4,'value_type': 'int'},
                {'value': base_number, "db_number": 260, 'offset': address+6, 'value_type': 'int'},
                {'value': source_target, "db_number": 260, 'offset': address+8, 'value_type': 'dint'},
                {'value': new_target, "db_number": 260, 'offset': address+12, 'value_type': 'dint'},
                {'value': location_number,"db_number": 260,'offset': address+16,'value_type': 'dint'},
                {'value': empty_location, "db_number": 260, 'offset': address+20, 'value_type': 'dint'},
                {'value': pack_number_find_code, "db_number": 260, 'offset': address+24,"string_max_len": 18,'value_type': 'string'},
                {'value': pack_barcode,"db_number": 260,'offset': address+46,"string_max_len": 18,'value_type': 'string'},

                {'value': info_goods, "db_number": 260, 'offset': address+68, 'bit_index': 0, 'value_type': 'bool'},
                {'value': info_cancel, "db_number": 260, 'offset': address+68, 'bit_index': 1, 'value_type': 'bool'},
                {'value': info_fixed_pack_number, "db_number": 260, 'offset': address+68, 'bit_index': 2, 'value_type': 'bool'},
                {'value': info_fixed_pack_barcode, "db_number": 260, 'offset': address+68, 'bit_index': 3, 'value_type': 'bool'},
                {'value': info_base_number, "db_number": 260, 'offset': address+70, 'value_type': 'int'},
                {'value': info_pack_number, "db_number": 260, 'offset': address+72, 'value_type': 'int'},
                {'value': info_location_number, "db_number": 260, 'offset': address+74, 'value_type': 'dint'},
                {'value': info_pack_barcode, "db_number": 260, 'offset': address+78, "string_max_len": 18, 'value_type': 'string'}

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

    @api.model
    def system_operate_read_write(self):

        self.online_control_exchange()
        self.task_status_changed()



    def online_control_exchange(self):
        control_system = self.env['warehouse.control.system'].search([], limit=1)

        online_update = control_system.online_update
        online_control = control_system.online_control
        online_update_bit = {}
        online_control_bit = {}
        for i in range(16):  # 检查前16位
            online_update_bit[f'bit_{i}'] = bool((online_update >> i) & 1)
        for i in range(16):  # 检查前16位
            online_control_bit[f'bit_{i}'] = bool((online_control >> i) & 1)

        # 构建新的online_download值
        new_online_control = online_control

        if control_system.netdata:

            if online_update_bit['bit_1']:
                self.storage_information_read(102)
                new_online_control = new_online_control | (1 << 1)
            else:
                new_online_control = new_online_control & ~(1 << 1)

            if online_update_bit['bit_2']:
                self.stacker_information_read(134)
                new_online_control = new_online_control | (1 << 2)
            else:
                new_online_control = new_online_control & ~(1 << 2)

            if online_update_bit['bit_3']:
                self.move_store_information_read(166)
                new_online_control = new_online_control | (1 << 3)
            else:
                new_online_control = new_online_control & ~(1 << 3)

            if online_update_bit['bit_4']:
                self.entrance1_information_read(198)
                new_online_control = new_online_control | (1 << 4)
            else:
                new_online_control = new_online_control & ~(1 << 4)

            if online_update_bit['bit_5']:
                self.entrance2_information_read(230)
                new_online_control = new_online_control | (1 << 5)
            else:
                new_online_control = new_online_control & ~(1 << 5)

            if online_update_bit['bit_6']:
                self.update_information_read(0)
                new_online_control = new_online_control | (1 << 6)
            else:
                new_online_control = new_online_control & ~(1 << 6)

            if online_update_bit['bit_7']:
                self.delete_information_read(32)
                new_online_control = new_online_control | (1 << 7)
            else:
                new_online_control = new_online_control & ~(1 << 7)

            if online_update_bit['bit_8']:
                self.reset_pc_command()
                new_online_control = new_online_control | (1 << 8)
            else:
                new_online_control = new_online_control & ~(1 << 8)

            # 只有在值发生变化时才写入数据库

            if online_control != new_online_control:
                # control_system.write({'online_control': new_online_control})
                # time.sleep(0.12)
                # print('online control', new_online_control)
                # control_system.write({'online_control': new_online_control})

                max_retries = 5
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        control_system.write({'online_control': new_online_control})
                        break
                    except Exception as e:
                        if "由于同步更新而无法串行访问" in str(e) or "could not serialize access" in str(e):
                            retry_count += 1
                            if retry_count >= max_retries:
                                _logger.warning(f"Failed to update online_control after {max_retries} retries: {str(e)}")
                                raise
                            else:
                                # 等待随机时间后重试
                                time.sleep(0.1 * retry_count + 0.1 * (hash(str(control_system.id)) % 10) / 10)
                                _logger.warning(f"Retrying update online_control due to serialization conflict, attempt {retry_count}")
                        else:
                            raise


    def reset_pc_command(self):
        record = self.browse(1)
        # 检查是否有字段从True变为False
        changed_fields = {}

        if record.move_stock:
            record.write({'move_stock': False})
            changed_fields['move_stock'] = False
        if record.store:
            record.write({'store': False})
            changed_fields['store'] = False
        if record.outbound:
            record.write({'outbound': False})
            changed_fields['outbound'] = False
        if record.return_store:
            record.write({'return_store': False})
            changed_fields['return_store'] = False

        # 如果有字段从True变为False，发送到频道
        if changed_fields:
            try:

                self.env['bus.bus']._sendone(
                    channel_with_db(self.env.cr.dbname, 'warehouse_data_update'),
                    'warehouse.data_update',
                    {
                        'model': 'warehouse.system.operate',
                        'id': record.id,
                        'changed_fields': changed_fields
                    }
                )

            except Exception as e:
                _logger.error("Failed to send command status update notification: %s", str(e))

    def task_status_changed(self):
        record = self.browse(1)
        control_system = self.env['warehouse.control.system'].search([], limit=1)
        self.netcontrol = control_system.netcontrol
        self.netdata = control_system.netdata
        self.auto_ready = control_system.auto_ready

        estate_status_map = {
            1: 'start',
            2: 'reach_source_target',
            3: 'take_finish',
            4: 'reach_new_target',
            5: 'feed_finish',
            6: 'finish',
            7: 'idle'
        }

        new_status = estate_status_map.get(control_system.estate, 'idle')
        old_status = record.status

        # 检查状态是否改变
        status_changed = old_status != new_status
        netcontrol_changed = record.netcontrol != control_system.netcontrol
        netdata_changed = record.netdata != control_system.netdata
        auto_ready_changed = record.auto_ready != control_system.auto_ready

        changed_fields = {}

        # 如果状态发生改变，则更新并记录
        if status_changed:
            record.status = new_status
            changed_fields['status'] = new_status

        # 如果netcontrol发生改变，则更新并记录
        if netcontrol_changed:
            record.netcontrol = control_system.netcontrol
            changed_fields['netcontrol'] = control_system.netcontrol

        # 如果netdata发生改变，则更新并记录
        if netdata_changed:
            record.netdata = control_system.netdata
            changed_fields['netdata'] = control_system.netdata

        if auto_ready_changed:
            record.auto_ready = control_system.auto_ready
            changed_fields['auto_ready'] = control_system.auto_ready

        # 只有当有字段真正改变时才发送通知
        if changed_fields:

            try:
                # 当状态发生变化时发送消息到频道
                self.env['bus.bus']._sendone(
                    channel_with_db(self.env.cr.dbname, 'warehouse_data_update'),
                    'warehouse.data_update',
                    {
                        'model': 'warehouse.system.operate',
                        'id': record.id,
                        'changed_fields': changed_fields
                    }
                )
            except Exception as e:
                _logger.error("Failed to send status update notification: %s", str(e))

    def storage_information_write(self, address):
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
                {'value': storage_goods_status,"db_number": 260,'offset': address,'bit_index': 0,'value_type': 'bool'},
                {'value': storage_base_number,"db_number": 260,'offset': address+2,'value_type': 'int'},
                {'value': storage_pack_number,"db_number": 260,'offset': address+4,'value_type': 'int'},
                {'value': storage_location_number,"db_number": 260,'offset': address+6,'value_type': 'dint'},
                {'value': storage_pack_barcode,"db_number": 260,'offset': address+10,"string_max_len": 18,'value_type': 'string'}
            ]
            for data in data_list:
                PlcClient().db_number_write(data)
        except Exception as e:
            _logger.error(f"库位信息写入失败！: {str(e)}")
            raise
    def stacker_information_write(self, address):
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
                {'value': stacker_goods_status, "db_number": 260, 'bit_index': address, 'value_type': 'bool', },
                {'value': stacker_base_number, "db_number": 260, 'offset': address+2, 'value_type': 'int'},
                {'value': stacker_pack_number, "db_number": 260, 'offset': address+4, 'value_type': 'int'},
                {'value': stacker_location_number, "db_number": 260, 'offset': address+6, 'value_type': 'dint'},
                {'value': stacker_pack_barcode, "db_number": 260, 'offset': address+10, "string_max_len": 18,
                 'value_type': 'string'}
            ]
            for data in data_list:
                PlcClient().db_number_write(data)
        except Exception as e:
            _logger.error(f"库位信息写入失败！: {str(e)}")
            raise
    def move_store_information_write(self, address):
        """传递到PLC进行写入"""
        # 提取字段值
        move_store_goods_status = self.move_store_goods_status
        move_store_base_number = self.move_store_base_number
        move_store_pack_number = self.move_store_pack_number
        move_store_location_number = self.move_store_location_number
        move_store_pack_barcode = self.move_store_pack_barcode
        # plc_client = PlcClient()
        try:
            # 批量写入
            data_list = [
                {'value': move_store_goods_status, "db_number": 260, 'bit_index': address, 'value_type': 'bool', },
                {'value': move_store_base_number, "db_number": 260, 'offset': address+2, 'value_type': 'int'},
                {'value': move_store_pack_number, "db_number": 260, 'offset': address+4, 'value_type': 'int'},
                {'value': move_store_location_number, "db_number": 260, 'offset': address+6, 'value_type': 'dint'},
                {'value': move_store_pack_barcode, "db_number": 260, 'offset': address+10, "string_max_len": 18,
                 'value_type': 'string'}
            ]
            for data in data_list:
                PlcClient().db_number_write(data)
        except Exception as e:
            _logger.error(f"库位信息写入失败！: {str(e)}")
            raise

    def entrance1_information_write(self, address):
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
                {'value': entrance1_goods_status, "db_number": 260, 'bit_index': address, 'value_type': 'bool', },
                {'value': entrance1_base_number, "db_number": 260, 'offset': address+2, 'value_type': 'int'},
                {'value': entrance1_pack_number, "db_number": 260, 'offset': address+4, 'value_type': 'int'},
                {'value': entrance1_location_number, "db_number": 260, 'offset': address+6, 'value_type': 'dint'},
                {'value': entrance1_pack_barcode, "db_number": 260, 'offset': address+10, "string_max_len": 18,
                 'value_type': 'string'}
            ]
            for data in data_list:
                PlcClient().db_number_write(data)
        except Exception as e:
            _logger.error(f"库位信息写入失败！: {str(e)}")
            raise
    def entrance2_information_write(self, address):
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
                {'value': entrance2_goods_status, "db_number": 260, 'bit_index': address, 'value_type': 'bool', },
                {'value': entrance2_base_number, "db_number": 260, 'offset': address+2, 'value_type': 'int'},
                {'value': entrance2_pack_number, "db_number": 260, 'offset': address+4, 'value_type': 'int'},
                {'value': entrance2_location_number, "db_number": 260, 'offset': address+6, 'value_type': 'dint'},
                {'value': entrance2_pack_barcode, "db_number": 260, 'offset': address+10, "string_max_len": 18,
                 'value_type': 'string'}
            ]
            for data in data_list:
                PlcClient().db_number_write(data)
        except Exception as e:
            _logger.error(f"库位信息写入失败！: {str(e)}")
            raise

    def _information_read(self, address):
        """读取测试-批量"""
        results = [
            # 库位有货，序号，框号，库位号，1-5
            {'db_number': 260, 'offset': address, 'value_type': 'bool', 'bit_index': 0},
            {'db_number': 260, 'offset': address + 2, 'value_type': 'int'},
            {'db_number': 260, 'offset': address + 4, 'value_type': 'int'},
            {'db_number': 260, 'offset': address + 6, 'value_type': 'dint'},
            {'db_number': 260, 'offset': address + 10, 'value_type': 'string', "string_max_len": 18},

            # 堆高机，框号，库位号，框条码， 6-10
            {'db_number': 260, 'offset': address + 32, 'value_type': 'bool', 'bit_index': 0},
            {'db_number': 260, 'offset': address + 34, 'value_type': 'int'},
            {'db_number': 260, 'offset': address + 36, 'value_type': 'int'},
            {'db_number': 260, 'offset': address + 38, 'value_type': 'dint'},
            {'db_number': 260, 'offset': address + 42, 'value_type': 'string', "string_max_len": 18},

            # 出入口1，框号，库位号，框条码， 11-15
            {'db_number': 260, 'offset': address + 64, 'value_type': 'bool', 'bit_index': 0},
            {'db_number': 260, 'offset': address + 66, 'value_type': 'int'},
            {'db_number': 260, 'offset': address + 68, 'value_type': 'int'},
            {'db_number': 260, 'offset': address + 70, 'value_type': 'dint'},
            {'db_number': 260, 'offset': address + 74, 'value_type': 'string', "string_max_len": 18},

            # 出入口2，框号，库位号，框条码， 16-20
            {'db_number': 260, 'offset': address + 96, 'value_type': 'bool', 'bit_index': 0},
            {'db_number': 260, 'offset': address + 98, 'value_type': 'int'},
            {'db_number': 260, 'offset': address + 100, 'value_type': 'int'},
            {'db_number': 260, 'offset': address + 102, 'value_type': 'dint'},
            {'db_number': 260, 'offset': address + 106, 'value_type': 'string', "string_max_len": 18},

            # 移库，框号，库位号，框条码， 21-25
            {'db_number': 260, 'offset': address + 128, 'value_type': 'bool', 'bit_index': 0},
            {'db_number': 260, 'offset': address + 130, 'value_type': 'int'},
            {'db_number': 260, 'offset': address + 132, 'value_type': 'int'},
            {'db_number': 260, 'offset': address + 134, 'value_type': 'dint'},
            {'db_number': 260, 'offset': address + 138, 'value_type': 'string', "string_max_len": 18},

        ]
        num = 0
        values_to_write = {}
        for result in results:
            num += 1
            value = PlcClient().db_number_read(result)
            # store，1-5
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

            # stacker，6-10
            elif num == 6:
                values_to_write['stacker_goods_status'] = value
            elif num == 7:
                values_to_write['stacker_base_number'] = value
            elif num == 8:
                values_to_write['stacker_pack_number'] = value
            elif num == 9:
                values_to_write['stacker_location_number'] = value
            elif num == 10:
                values_to_write['stacker_pack_barcode'] = value

            # entrance1，11-15
            elif num == 11:
                values_to_write['entrance1_goods_status'] = value
            elif num == 12:
                values_to_write['entrance1_base_number'] = value
            elif num == 13:
                values_to_write['entrance1_pack_number'] = value
            elif num == 14:
                values_to_write['entrance1_location_number'] = value
            elif num == 15:
                values_to_write['entrance1_pack_barcode'] = value
            # entrance2，16-20
            elif num == 16:
                values_to_write['entrance2_goods_status'] = value
            elif num == 17:
                values_to_write['entrance2_base_number'] = value
            elif num == 18:
                values_to_write['entrance2_pack_number'] = value
            elif num == 19:
                values_to_write['entrance2_location_number'] = value
            elif num == 20:
                values_to_write['entrance2_pack_barcode'] = value
            # move store，21 - 25
            elif num == 21:
                values_to_write['move_store_goods_status'] = value
            elif num == 22:
                values_to_write['move_store_base_number'] = value
            elif num == 23:
                values_to_write['move_store_pack_number'] = value
            elif num == 24:
                values_to_write['move_store_location_number'] = value
            elif num == 25:
                values_to_write['move_store_pack_barcode'] = value

        if values_to_write:
            record = self.browse(1)
            # 检查哪些字段发生了变化
            changed_fields = {}
            for field, new_value in values_to_write.items():
                old_value = getattr(record, field)
                if old_value != new_value:
                    changed_fields[field] = new_value
                    _logger.info(f"field {field} changed，old value：{old_value}，new value：{new_value}")
            # 只有当有字段发生变化时才更新并发送通知
            if changed_fields:
                record.write(changed_fields)

                # 发送通知到前端，只包含变化的字段
                self.env['bus.bus']._sendone(
                    channel_with_db(self.env.cr.dbname, 'warehouse_data_update'),
                    'warehouse.data_update',
                    {
                        'model': 'warehouse.system.operate',
                        'id': record.id,
                        'changed_fields': changed_fields
                    }
                )

    def test_button(self):
        self.update_information_read(0)

    def update_information_read(self, address):

        results = [
            # 库位有货，序号，框号，库位号，框条码
            {'db_number': 262, 'offset': address, 'value_type': 'bool', 'bit_index': 0},
            {'db_number': 262, 'offset': address+2, 'value_type': 'int'},
            {'db_number': 262, 'offset': address+4, 'value_type': 'int'},
            {'db_number': 262, 'offset': address+6, 'value_type': 'dint'},
            {'db_number': 262, 'offset': address+10, 'value_type': 'string', "string_max_len": 18},
        ]
        num = 0
        update_location_number = 0
        values_to_write = {}
        for result in results:
            num += 1
            value = PlcClient().db_number_read(result)
            if num == 1:
                values_to_write['goods_status'] = value
            # elif num == 2:
            #     values_to_write['base_number'] = value
            elif num == 3:
                values_to_write['pack_number'] = value
            elif num == 4:
                values_to_write['location_number'] = value
                update_location_number = value
            elif num == 5:
                values_to_write['pack_barcode'] = value

        if values_to_write:

            storage_record = self.env['warehouse.location.information'].search(
                [('location_number', '=', update_location_number),
                       ('location_number', '!=', 0)], limit=1)
            if storage_record:
                storage_record.write(values_to_write)

            else:
               _logger.info("The storage location does not exist, no updated data!")

    def delete_information_read(self, address):

        results = [
            # 库位有货，序号，框号，库位号，框条码
            {'db_number': 262, 'offset': address, 'value_type': 'bool', 'bit_index': 0},
            {'db_number': 262, 'offset': address+2, 'value_type': 'int'},
            {'db_number': 262, 'offset': address+4, 'value_type': 'int'},
            {'db_number': 262, 'offset': address+6, 'value_type': 'dint'},
            {'db_number': 262, 'offset': address+10, 'value_type': 'string', "string_max_len": 18},
        ]
        num = 0
        update_location_number = 0
        values_to_write = {}
        for result in results:
            num += 1
            value = PlcClient().db_number_read(result)
            if num == 1:
                values_to_write['goods_status'] = value
            # elif num == 2:
            #     values_to_write['base_number'] = value
            elif num == 3:
                values_to_write['pack_number'] = value
            elif num == 4:
                values_to_write['location_number'] = value
                update_location_number = value
            elif num == 5:
                values_to_write['pack_barcode'] = value

        if values_to_write:

            storage_record = self.env['warehouse.location.information'].search(
                [('location_number', '=', update_location_number),
                       ('location_number', '!=', 0)], limit=1)
            if storage_record:
                storage_record.write(values_to_write)

            else:
               _logger.info("The storage location does not exist, no updated data!")


    def storage_information_read(self, address):
        """读取测试-批量"""
        results = [
            # 库位有货，序号，框号，库位号，框条码
            {'db_number': 260, 'offset': address, 'value_type': 'bool', 'bit_index': 0},
            {'db_number': 260, 'offset': address+2, 'value_type': 'int'},
            {'db_number': 260, 'offset': address+4, 'value_type': 'int'},
            {'db_number': 260, 'offset': address+6, 'value_type': 'dint'},
            {'db_number': 260, 'offset': address+10, 'value_type': 'string', "string_max_len": 18},
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
        # if values_to_write:
        #     record = self.browse(1)
        #     # record = self.env['warehouse.system.operate'].browse(1)
        #     record.write(values_to_write)

        if values_to_write:
            record = self.browse(1)
            # 检查哪些字段发生了变化
            changed_fields = {}
            for field, new_value in values_to_write.items():
                old_value = getattr(record, field)
                if old_value != new_value:
                    changed_fields[field] = new_value
                    _logger.info(f"field {field} changed，old value：{old_value}，new value：{new_value}")
            # 只有当有字段发生变化时才更新并发送通知
            if changed_fields:
                record.write(changed_fields)

                # 发送通知到前端，只包含变化的字段
                self.env['bus.bus']._sendone(
                    channel_with_db(self.env.cr.dbname, 'warehouse_data_update'),
                    'warehouse.data_update',
                    {
                        'model': 'warehouse.system.operate',
                        'id': record.id,
                        'changed_fields': changed_fields
                    }
                )

    def stacker_information_read(self, address):
        """读取测试-批量"""
        results = [
            #库位有货，框号，库位号，框条码
            {'db_number': 260, 'offset': address, 'value_type': 'bool', 'bit_index':0},
            {'db_number': 260, 'offset': address+2, 'value_type': 'int'},
            {'db_number': 260, 'offset': address+4, 'value_type': 'int'},
            {'db_number': 260, 'offset': address+6, 'value_type': 'dint'},
            {'db_number': 260, 'offset': address+10, 'value_type': 'string', "string_max_len": 18},
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
            # 检查哪些字段发生了变化
            changed_fields = {}
            for field, new_value in values_to_write.items():
                old_value = getattr(record, field)
                if old_value != new_value:
                    changed_fields[field] = new_value
                    _logger.info(f"field {field} changed，old value：{old_value}，new value：{new_value}")
            # 只有当有字段发生变化时才更新并发送通知
            if changed_fields:
                record.write(changed_fields)

                # 发送通知到前端，只包含变化的字段
                self.env['bus.bus']._sendone(
                    channel_with_db(self.env.cr.dbname, 'warehouse_data_update'),
                    'warehouse.data_update',
                    {
                        'model': 'warehouse.system.operate',
                        'id': record.id,
                        'changed_fields': changed_fields
                    }
                )
    def move_store_information_read(self, address):
        """读取测试-批量"""
        results = [
            #库位有货，框号，库位号，框条码
            {'db_number': 260, 'offset': address, 'value_type': 'bool', 'bit_index':0},
            {'db_number': 260, 'offset': address+2, 'value_type': 'int'},
            {'db_number': 260, 'offset': address+4, 'value_type': 'int'},
            {'db_number': 260, 'offset': address+6, 'value_type': 'dint'},
            {'db_number': 260, 'offset': address+10, 'value_type': 'string', "string_max_len": 18},
        ]
        num = 0
        values_to_write = {}
        for result in results:
            num += 1
            value = PlcClient().db_number_read(result)
            if num == 1:
                values_to_write['move_store_goods_status'] = value
            elif num == 2:
                values_to_write['move_store_base_number'] = value
            elif num == 3:
                values_to_write['move_store_pack_number'] = value
            elif num == 4:
                values_to_write['move_store_location_number'] = value
            elif num == 5:
                values_to_write['move_store_pack_barcode'] = value
        if values_to_write:
            record = self.browse(1)
            # 检查哪些字段发生了变化
            changed_fields = {}
            for field, new_value in values_to_write.items():
                old_value = getattr(record, field)
                if old_value != new_value:
                    changed_fields[field] = new_value
                    _logger.info(f"field {field} changed，old value：{old_value}，new value：{new_value}")
            # 只有当有字段发生变化时才更新并发送通知
            if changed_fields:
                record.write(changed_fields)

                # 发送通知到前端，只包含变化的字段
                self.env['bus.bus']._sendone(
                    channel_with_db(self.env.cr.dbname, 'warehouse_data_update'),
                    'warehouse.data_update',
                    {
                        'model': 'warehouse.system.operate',
                        'id': record.id,
                        'changed_fields': changed_fields
                    }
                )
    def entrance1_information_read(self, address):
        """读取测试-批量"""
        results = [
            #库位有货，框号，库位号，框条码
            {'db_number': 260, 'offset': address, 'value_type': 'bool', 'bit_index':0},
            {'db_number': 260, 'offset': address+2, 'value_type': 'int'},
            {'db_number': 260, 'offset': address+4, 'value_type': 'int'},
            {'db_number': 260, 'offset': address+6, 'value_type': 'dint'},
            {'db_number': 260, 'offset': address+10, 'value_type': 'string', "string_max_len": 18},
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
            # 检查哪些字段发生了变化
            changed_fields = {}
            for field, new_value in values_to_write.items():
                old_value = getattr(record, field)
                if old_value != new_value:
                    changed_fields[field] = new_value
                    _logger.info(f"field {field} changed，old value：{old_value}，new value：{new_value}")
            # 只有当有字段发生变化时才更新并发送通知
            if changed_fields:
                record.write(changed_fields)

                # 发送通知到前端，只包含变化的字段
                self.env['bus.bus']._sendone(
                    channel_with_db(self.env.cr.dbname, 'warehouse_data_update'),
                    'warehouse.data_update',
                    {
                        'model': 'warehouse.system.operate',
                        'id': record.id,
                        'changed_fields': changed_fields
                    }
                )
    def entrance2_information_read(self, address):
        """读取测试-批量"""
        results = [
            #库位有货，框号，库位号，框条码
            {'db_number': 260, 'offset': address, 'value_type': 'bool', 'bit_index':0},
            {'db_number': 260, 'offset': address+2, 'value_type': 'int'},
            {'db_number': 260, 'offset': address+4, 'value_type': 'int'},
            {'db_number': 260, 'offset': address+6, 'value_type': 'dint'},
            {'db_number': 260, 'offset': address+10, 'value_type': 'string', "string_max_len": 18},
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
            # 检查哪些字段发生了变化
            changed_fields = {}
            for field, new_value in values_to_write.items():
                old_value = getattr(record, field)
                if old_value != new_value:
                    changed_fields[field] = new_value
                    _logger.info(f"field {field} changed，old value：{old_value}，new value：{new_value}")
            # 只有当有字段发生变化时才更新并发送通知
            if changed_fields:
                record.write(changed_fields)

                # 发送通知到前端，只包含变化的字段
                self.env['bus.bus']._sendone(
                    channel_with_db(self.env.cr.dbname, 'warehouse_data_update'),
                    'warehouse.data_update',
                    {
                        'model': 'warehouse.system.operate',
                        'id': record.id,
                        'changed_fields': changed_fields
                    }
                )


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

    def reload_data_button(self):
        self.check_permissions()
        self.target_data_check()
        self._onchange_pack_number()


    def move_stock_button(self):
        record = self.browse(1)
        self.check_permissions()
        self.target_data_check()
        if record.allow_move_stock:
            record.move_stock = not record.move_stock
            record.store = False
            record.outbound =  False
            record.return_store =  False
            log_message = f"{record.current_user_name}执行移库:从{record.source_target}移到库位{record.new_target} ！"
            _logger.info(log_message)
            record.log_operation(log_message)
        else:
            raise UserError("不允许执行移库命令！")

    def store_button(self):
        record = self.browse(1)
        self.check_permissions()
        self.target_data_check()
        if record.allow_store:
            record.move_stock = False
            record.store = not record.store
            record.outbound =  False
            record.return_store =  False
            self.command_button_write()
            log_message = f"{record.current_user_name}执行入库:从{record.source_target}移到库位{record.new_target} ！"
            _logger.info(log_message)
            record.log_operation(log_message)
        else:
            raise UserError(f"不允许执行入库命令！")

    def outbound_button(self):
        record = self.browse(1)
        self.check_permissions()
        self.target_data_check()
        if record.allow_outbound:
            record.move_stock = False
            record.store = False
            record.outbound = not record.outbound
            record.return_store = False
            self.command_button_write()
            log_message = f"{record.current_user_name}执行出库:从{record.source_target}移到{record.entrance}：{record.new_target} ！"
            _logger.info(log_message)
            record.log_operation(log_message)
        else:
            raise UserError(f"不允许执行出库命令！")
    def return_store_button(self):
        record = self.browse(1)
        self.check_permissions()
        self.target_data_check()
        if record.allow_return:
            record.move_stock = False
            record.store =  False
            record.outbound =  False
            record.return_store = not record.return_store
            self.command_button_write()
            log_message = f"{record.current_user_name}执行返库:从{record.source_target}移到库位{record.new_target} ！"
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
    def check_permissions(self):
        control_system = self.env['warehouse.control.system'].search([], limit=1)
        task_running = control_system.task_running
        net_control = control_system.netcontrol
        record = self.browse(1)
        if not record.Operation_permissions:
            raise UserError("没有权限执行此操作！")
        if not net_control:
            raise UserError("没远控权限，不允许执行控制命令！")
        if task_running:
            raise UserError("任务正在运行中！")


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