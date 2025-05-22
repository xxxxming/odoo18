# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
import threading
import struct
from apscheduler.schedulers.background import BackgroundScheduler

from odoo.fields import Many2one
from .plc_connect import PlcClient
from .wharehouse_communication import New_Public_PlcInterfaces

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
    _name = 'control.system.operate'
    _description = 'control system operate'
    workshop = fields.Char(string="车间代号")
    line = fields.Char(string="线体代号")
    machine = fields.Char(string="机台代号")
    emergency_stop = fields.Boolean(string="紧急停止", default=False)
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
    storage_fixed_pack_number = fields.Boolean(string='绑定框号')
    storage_fixed_pack_barcode = fields.Boolean(string='绑定条码')
    storage_pack_number = fields.Integer(string='框号')
    storage_base_number = fields.Integer(string='库位编号')
    storage_location_number = fields.Integer(string='库位号')
    storage_pack_barcode = fields.Char(string='框条码')

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

    def initialize_data(self):
        """
        hook调用
        """
        code = New_Public_PlcInterfaces().initialize_data_start()
        #self.env['storage_goods_status'] = code
        self.storage_goods_status = code
        _logger.info(f'测试{code}')
        pass

    def start_plc_scheduler(self):
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
        _logger.info(f'{row_data.get("value_type")}查询结果：{value}')
        return value

    def update_plc(self):
        """传递到PLC进行写入"""
        # 单独写入
        # 库位有货
        read_storage_goods_status = self.storage_goods_status
        data = {
            'value' : read_storage_goods_status,
            'bit_index': 0,
            'value_type' : 'bool'
        }
        PlcClient().set_db_number_write(data)
        # 取消库位
        read_storage_goods_cancel = self.storage_goods_cancel
        if read_storage_goods_cancel == None:
            read_storage_goods_cancel = False
        data = {
            'value': read_storage_goods_cancel,
            'bit_index': 2,
            'value_type': 'bool'
        }
        PlcClient().set_db_number_write(data)
        # 框号
        read_storage_pack_number = self.storage_pack_number
        data = {
            'value': read_storage_pack_number,
            'offset': 2,
            'value_type': 'int'
        }
        PlcClient().set_db_number_write(data)
        # 库位编号
        read_storage_base_number = self.storage_base_number
        data = {
            'value': read_storage_base_number,
            'offset': 4,
            'value_type': 'int'
        }
        PlcClient().set_db_number_write(data)
        # 库位号
        read_storage_location_number = self.storage_location_number
        data = {
            'value': read_storage_location_number,
            'offset': 6,
            'value_type': 'int'
        }
        PlcClient().set_db_number_write(data)
        # 框条码
        stacker_pack_barcode = self.stacker_pack_barcode
        data = {
            'value': stacker_pack_barcode,
            'offset': 14,
            "string_max_len": 8,
            'value_type': 'string'
        }
        PlcClient().set_db_number_write(data)
        # 对某个DB内进行批量写入



    def fetch_plc(self):
        """读取测试-批量"""

        # 读取库位信息例子
        results = [
            # 库位有货
            {'db_number': 262, 'offset': 0, 'value_type': 'bool', 'bit_index':0},
            # 框号
            {'db_number': 262, 'offset': 2, 'value_type': 'int'},
            # 库位编号
            {'db_number': 262, 'offset': 3, 'value_type': 'int'},
            # 库位号
            {'db_number': 262, 'offset': 4, 'value_type': 'int'},
            # 框条码
            {'db_number': 262, 'offset': 5, 'value_type': 'int'},
        ]
        for result in results:
            value = self.batch_read_plc(result)


    def emergency_button(self):
        code = self.env['plc.interface'].read_emergency_stop_state()
        for record in self:
            # 不允许远程控制状态下以以plc状态为主
            pc_code = record.emergency_stop
            if code:
                # 不相等状态下，以plc状态为主
                if pc_code != code:
                    record.emergency_stop = pc_code
                else:
                    record.emergency_stop = code
            else:
                record.emergency_stop = False

            _logger.info(record.emergency_stop)
            record.emergency_stop = pc_code

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


    @api.model
    def inventory_information_write(self, bits0, bits1, value1, value2, value3, value4,
                                    db_number: int = 0, address: int = 0, str_length: int = 20,
                                    rack: int = 0, slot: int = 1) -> bool:
        """
        批量插入plc
        param: plc_ip
        param: area （只需要DB， M、Q不需要）
        param: value [bool, int, float, str, bytes, bytearray]
        param: db_number
        param: address 【西门子自占用2个字节】
        param: bit_offset 【位偏移（0-7，仅布尔类型需要）】
        param: data_type 数据类型
        param: str_length 字符串总长度（仅字符串类型需要）
        param: rack 默认机架号
        param: slot 默认插槽号
        """
        #     raise ConnectionError("PLC连接失败")
        client = self.PlcClient.connect_plc()
        if not client:
            pass
        try:
            current_data = client.db_read(db_number, address, 1)
            current_byte = current_data[0]
            if bits0:
                new_byte = current_byte | (1 << 0)
            else:
                new_byte = current_byte & ~(1 << 0)
            data_to_write = bytearray([new_byte])
            client.db_write(db_number, address, data_to_write)

            current_data = client.db_read(db_number, address, 1)
            current_byte = current_data[0]
            if bits1:
                new_byte = current_byte | (1 << 1)
            else:
                new_byte = current_byte & ~(1 << 1)
            data_to_write = bytearray([new_byte])
            client.db_write(db_number, address, data_to_write)

            data_to_write = bytearray(struct.pack('>h', value1))
            client.db_write(db_number, address + 2, data_to_write)

            data_to_write = bytearray(struct.pack('>h', value2))
            client.db_write(db_number, address + 4, data_to_write)

            data_to_write = bytearray(struct.pack('>I', value3))
            client.db_write(db_number, address + 10, data_to_write)

            # 字符串类型（西门子格式）
            if not isinstance(value4, str):
                raise TypeError("str类型需要字符串值")
            if str_length < len(value4):
                raise ValueError("字符串长度超过定义长度")
            encoded_str = value4.encode('utf-8')
            data_to_write = bytearray(struct.pack(
                f'>BB{str_length}s',  # 格式：最大长度(2字节) + 实际长度(2字节) + 内容
                str_length,
                len(encoded_str),
                encoded_str.ljust(str_length, b'\x00')
            ))
            client.db_write(db_number, address + 14, data_to_write)
            return True
        except Exception as e:
            return False


