# -*- coding: utf-8 -*-
import logging
from email.policy import default

import odoo
from odoo import models, fields, api, SUPERUSER_ID
import threading
from odoo import http
from odoo.addons.test_convert.tests.test_env import record
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


def read_information():
    """读取测试-批量"""
    # 读取库位信息例子
    results = [
        # 库位有货
        {'db_number': 202,'start_address': 0, 'value_type': 'bool', 'bit_index':0},
        # 框号
    ]
    for result in results:
        # value = self.batch_read_plc(result)
        value =  PlcClient().set_db_number_read(result)
        return value


class ControlSystemOperate(models.Model):

    # _inherit = 'system.control'
    _name = 'control.system.operate'
    _description = 'control system operate'

    refresh_trigger = fields.Boolean(
        string="视图重载",default=False,
        help="When set to True, triggers a view refresh via bus notification")

    workshop = fields.Char(string="车间代号")
    line = fields.Char(string="产线代号")
    machine = fields.Char(string="机台代号")
    # emergency_stop = fields.Boolean(string="紧急停止", default=False)
    control_id = Many2one('system.control',string='系统控制')
    pc_start = fields.Boolean(related='control_id.start',string='开始',store=True)
    # one_second = fields.Integer(string='一秒周期')
    emergency_stop = fields.Boolean(related='control_id.emergency_stop',string='紧急停止')
    manual_control = fields.Boolean(string="手动控制")
    auto_control = fields.Boolean(string="自动控制")
    stop = fields.Boolean(string="停止")
    pause = fields.Boolean(string="暂停")
    reset = fields.Boolean(string="复位")
    store = fields.Boolean(string="存储")
    outbound = fields.Boolean(string="出库")
    return_store = fields.Boolean(string="回库")
    allow_store = fields.Boolean(string="允许入库")
    allow_outbound = fields.Boolean(string="允许出库")
    allow_return = fields.Boolean(string="允许返库")
    pack_number = fields.Integer(string='框号')
    source_target = fields.Integer(string="源目标")
    new_target = fields.Integer(string="新目标")
    status = fields.Selection([
        ('idle', '空闲'),
        ('running', '运行中'),
        ('paused', '暂停'),
        ('stopped', '停止'),
        ('emergency', '紧急停止')
    ], string="状态", default='idle')
    # 展示框号
    show_storage_pack_number = fields.Integer(string='框号')

    storage_goods_status = fields.Boolean(string='库位有货')
    storage_goods_status_code = Many2one('plc.storage.interface', string='库位信息')
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
        # self.one_second = self.control_id.one_second
        # for record in self:
        #     if record.control_id:
        #         record.one_second = record.control_id.one_second
        #     else:
        #         record.one_second = 0  # 默认值或空值处理

        print("test_compute")

    @api.onchange('storage_goods_cancel')
    def _onchange_one_second(self):
        if self.storage_goods_status:
            self.status = 'idle'
        else:
            self.status = 'running'
        print(self.status)
        print(self.storage_pack_number)
        # self.one_second += 1
        # self.one_second = self.control_id.one_second
        print("test_onchange")
    def initialize_data(self):
        """
        hook调用
        """
        # code = New_Public_PlcInterfaces().initialize_data_start()
        #self.env['storage_goods_status'] = code
        # self.storage_goods_status = code
        # _logger.info(f'测试{code}')
        pass

    def start_plc_scheduler(self):
        # print(self.pc_start)
        _logger.info("开始启动定时任务测试")
        pass

    def read_write_plc_data(self):
        pass


    def _get_cron_record(self):

        """获取或创建定时任务记录"""
        pass
        # cron = self.env.ref('plc_interface.plc_sync_cron', raise_if_not_found=False)
        # if not cron:
        #     cron = self.env['ir.cron'].create({
        #         'name': 'PLC数据自动同步',
        #         'model_id': self.env.ref('plc_interface.model_plc_interface').id,
        #         'state': 'code',
        #         'code': 'model._cron_sync_plc_data()',
        #         'interval_number': self.cron_interval,
        #         'interval_type': 'minutes',
        #         'active': self.cron_active
        #     })
        #     self.env['ir.model.data'].create({
        #         'name': 'plc_sync_cron',
        #         'module': 'plc_interface',
        #         'model': 'ir.cron',
        #         'res_id': cron.id,
        #     })
        # return cron


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
                values_to_write['refresh_trigger'] = value
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
            # record = self.env['control.system.operate'].search([], limit=1)
            # current_record = self.read()
            # _logger.info("当前记录字段及值: %s", record)
        # 统一写入数据库，减少 I/O 次数
        if values_to_write:
            # print(values_to_write)
            # self.browse(1).write(values_to_write)
            record = self.browse(1)
            record.write(values_to_write)
            # record.write(self.refresh_trigger, True)

            print(values_to_write)

            # self.refresh_trigger = True

            # record.write({'refresh_trigger': True})
            # print(self.refresh_trigger)
            # self.write_refresh(values_to_write)
            record.write_refresh(values_to_write)


            # 显式刷新缓存，确保前端感知到字段变更
            # if record:
            #     record.modified([
            #         'storage_goods_status',
            #         'storage_base_number',
            #         'storage_pack_number',
            #         'storage_location_number',
            #         'storage_pack_barcode'
            #     ])
            #     record.env.flush_all()
            #     self.env.cr.commit()
                # _logger.info(values_to_write)
            print('refresh_trigger4', record.refresh_trigger)


        return values_to_write

    def write_refresh(self, vals):
        # res = super().write(vals)

        print('trigger1',vals['refresh_trigger'])
        if 'refresh_trigger' in vals and vals['refresh_trigger']:
            # 为每个记录发送单独的通知
            print('trigger2', vals['refresh_trigger'])
            print(self)
            if not self:
                print("self is empty or None")
            else:
                for record in self:

                    self._send_refresh_notification(record)
                    # 可选：立即重置触发器
                    # record.with_context(skip_refresh=True).write({'refresh_trigger': False})

                    # 🔍 打印所有从 vals 传入的字段和值
                    # for key, value in vals.items():
                    #     print(f"Key: {key}, Value: {value}")

                    refresh_trigger5 = record
                    print('trigger4',refresh_trigger5)

        return None

    def _send_refresh_notification(self, record):
        """发送总线通知"""
        notification = {
            'type': 'record_refresh',
            'model': self._name,
            'record_id': record.id,
            'timestamp': fields.Datetime.now(),
        }


        # 使用特定频道发送通知
        self.env['bus.bus']._sendone(
            self._get_record_channel(record),
            'record_refresh',
            notification
        )

        # data = record.read()
        # _logger.info("Record data: %s", data)

    def _get_record_channel(self, record):
        """生成记录特定频道名称"""
        return channel_with_db(
            self.env.cr.dbname,
            f'{self._name}.record.refresh.{record.id}'
        )



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

            # print(values_to_write)


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
            # print(values_to_write)
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
            # print(values_to_write)

    # @http.route('/my/model/pack_number', type='json', auth='user')
    # def real_update_val(self):
    #     """实时更新"""
    #     record = request.env['my.model'].sudo().browse(int(record_id))
    #     return {'pack_number': record.storage_pack_number}




    def emergency_button(self):
        # code = self.env['system.control']

        # 获取目标模型的第一条记录
        # target_record = self.env['system.control'].search([], limit=1)
        # _logger.info('target_record')
        # _logger.info(target_record)
        # if target_record:
        #     # 读取并切换字段状态
        #     target_record.emergency_stop = not target_record.emergency_stop
        #     # self.write({'emergency_stop': target_record.emergency_stop})
        #     #self.emergency_stop = target_record.emergency_stop
        #     _logger.info('模型测试')
        #     _logger.info(target_record.emergency_stop)
        #     for record in self:
        #         record.emergency_stop = True
        self.write({'emergency_stop': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',  # 强制刷新当前视图
        }

        # for record in self:
        #     record.emergency_stop = not record.emergency_stop
        # code = self.env['plc.interface'].read_emergency_stop_state()
        # for record in self:
        #     # 不允许远程控制状态下以以plc状态为主
        #     pc_code = record.emergency_stop
        #     if code:
        #         # 不相等状态下，以plc状态为主
        #         if pc_code != code:
        #             record.emergency_stop = pc_code
        #         else:
        #             record.emergency_stop = code
        #     else:
        #         record.emergency_stop = False
        #
        #     _logger.info(record.emergency_stop)
        #     record.emergency_stop = pc_code
        # print(target_record.emergency_stop)

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



    # @api.model
    # def inventory_information_write(self, bits0, bits1, value1, value2, value3, value4,
    #                                 db_number: int = 0, address: int = 0, str_length: int = 20,
    #                                 rack: int = 0, slot: int = 1) -> bool:
    #     """
    #     批量插入plc
    #     param: plc_ip
    #     param: area （只需要DB， M、Q不需要）
    #     param: value [bool, int, float, str, bytes, bytearray]
    #     param: db_number
    #     param: address 【西门子自占用2个字节】
    #     param: bit_offset 【位偏移（0-7，仅布尔类型需要）】
    #     param: data_type 数据类型
    #     param: str_length 字符串总长度（仅字符串类型需要）
    #     param: rack 默认机架号
    #     param: slot 默认插槽号
    #     """
        #     raise ConnectionError("PLC连接失败")
    #     client = self.PlcClient.connect_plc()
    #     if not client:
    #         pass
    #     try:
    #         current_data = client.db_read(db_number, address, 1)
    #         current_byte = current_data[0]
    #         if bits0:
    #             new_byte = current_byte | (1 << 0)
    #         else:
    #             new_byte = current_byte & ~(1 << 0)
    #         data_to_write = bytearray([new_byte])
    #         client.db_write(db_number, address, data_to_write)
    #
    #         current_data = client.db_read(db_number, address, 1)
    #         current_byte = current_data[0]
    #         if bits1:
    #             new_byte = current_byte | (1 << 1)
    #         else:
    #             new_byte = current_byte & ~(1 << 1)
    #         data_to_write = bytearray([new_byte])
    #         client.db_write(db_number, address, data_to_write)
    #
    #         data_to_write = bytearray(struct.pack('>h', value1))
    #         client.db_write(db_number, address + 2, data_to_write)
    #
    #         data_to_write = bytearray(struct.pack('>h', value2))
    #         client.db_write(db_number, address + 4, data_to_write)
    #
    #         data_to_write = bytearray(struct.pack('>I', value3))
    #         client.db_write(db_number, address + 10, data_to_write)
    #
    #         # 字符串类型（西门子格式）
    #         if not isinstance(value4, str):
    #             raise TypeError("str类型需要字符串值")
    #         if str_length < len(value4):
    #             raise ValueError("字符串长度超过定义长度")
    #         encoded_str = value4.encode('utf-8')
    #         data_to_write = bytearray(struct.pack(
    #             f'>BB{str_length}s',  # 格式：最大长度(2字节) + 实际长度(2字节) + 内容
    #             str_length,
    #             len(encoded_str),
    #             encoded_str.ljust(str_length, b'\x00')
    #         ))
    #         client.db_write(db_number, address + 14, data_to_write)
    #         return True
    #     except Exception as e:
    #         return False
    #
    # def write_storage_information(self):
    #     plc_interface = self.connect_plc()
    #     if not plc_interface:
    #         pass
    #     code = self.inventory_information_write(
    #         db_number=202,
    #         address=0,
    #         bits0=self.storage_goods_status,
    #         bits1=self.storage_goods_cancel,
    #         value1=self.storage_pack_number,
    #         value2=self.storage_base_number,
    #         value3=self.storage_location_number,
    #         value4=self.storage_pack_barcode,
    #     )

    # @api.model
    # def inventory_information_read(self,
    #                                db_number: int = 0, address: int = 0, str_length: int = 20,
    #                                rack: int = 0, slot: int = 1) -> bool:
    #     """
    #     批量插入plc
    #     param: plc_ip
    #     param: area （只需要DB， M、Q不需要）
    #     param: value [bool, int, float, str, bytes, bytearray]
    #     param: db_number
    #     param: address 【西门子自占用2个字节】
    #     param: bit_offset 【位偏移（0-7，仅布尔类型需要）】
    #     param: data_type 数据类型
    #     param: str_length 字符串总长度（仅字符串类型需要）
    #     param: rack 默认机架号
    #     param: slot 默认插槽号
    #     """

        # data_to_write1:int
        # 创建 PlcClient 实例
        # plc_client = PlcClient()
        # 连接 PLC
        # client = plc_client.connect_plc()
        # client = self.connect_plc()
        # if client is None:
        #     raise ConnectionError("PLC连接失败")
        #
        # try:
            # 写入一个字节位
            # if len(bits) != 8:
            #     raise ValueError("必须提供8个布尔值")
            # byte = 0
            # for i in range(8):
            #     if bits[i]:
            #         byte |= (1 << (7 - i))
            # data_to_write = bytearray([byte])

            # current_data = client.db_read(db_number, address, 1)
            # current_byte = current_data[0]
            # bit0 = bool(current_byte & (1 << 0))  # 获取第 0 位的状态
            #
            # bit1 = bool(current_byte & (1 << 1))  # 获取第 1 位的状态
            #
            # raw_data = client.db_read(db_number, address + 2, 2)
            # value1 = struct.unpack('>h', raw_data)[0]
            # # self.write({'value1': value1})
            # raw_data = client.db_read(db_number, address + 4, 2)
            # value2 = struct.unpack('>h', raw_data)[0]
            #
            # raw_data = client.db_read(db_number, address + 10, 4)
            # value3 = struct.unpack('>I', raw_data)[0]

            # # 字符串类型（西门子格式）
            # if not isinstance(value4, str):
            #     raise TypeError("str类型需要字符串值")
            # if str_length < len(value4):
            #     raise ValueError("字符串长度超过定义长度")
            # encoded_str = value4.encode('utf-8')
            # data_to_write = bytearray(struct.pack(
            #     f'>BB{str_length}s',  # 格式：最大长度(2字节) + 实际长度(2字节) + 内容
            #     str_length,
            #     len(encoded_str),
            #     encoded_str.ljust(str_length, b'\x00')
            # ))
            # client.db_write(db_number, address + 14, data_to_write)

            # raw_data = client.db_read(db_number, address + 14, str_length)
            # value4 = raw_data[2:2 + raw_data[1]].decode('utf-8').strip('\x00')
            # print(value4)
            # return {value3, 123, }
            # return True
    #         return {
    #             "bit0": bit0,
    #             'bit1': bit1,
    #             'value1': value1,
    #             'value2': value2,
    #             'value3': value3,
    #             'value4': value4,
    #         }
    #
    #     except Exception as e:
    #         return False
    #
    #     finally:
    #         if client.get_connected():
    #             client.disconnect()
    #
    # def read_storage_information(self):

        # plc_interface = self.connect_plc()
        # 创建 PlcClient 实例
        # plc_client = PlcClient()
        # 连接 PLC
        # client = plc_client.connect_plc()
        #
        # if not client:
        #     pass
        # code = self.inventory_information_read(
        #     db_number=202,
        #     address=0,
        # )
        # logging.info(code)
        # for result in self:
        #     result.storage_goods_status = code.get('bit0')
        #     result.storage_pack_number = code.get('value1')
        #     result.storage_base_number = code.get('value2')
        #     result.storage_location_number = code.get('value3')
        #     result.storage_pack_barcode = code.get('value4')
        # print(value)





