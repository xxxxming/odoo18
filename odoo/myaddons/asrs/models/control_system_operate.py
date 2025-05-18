# -*- coding: utf-8 -*-
import struct

import snap7
import logging
import time

from reportlab.lib.logger import infoOnce
from snap7.util import *
from odoo import models, fields, api
import odoo
from odoo.exceptions import ValidationError
from .plc_models import connect_plc

import threading
# import time
# from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from odoo import api, registry, SUPERUSER_ID
# import logging

_logger = logging.getLogger(__name__)

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

class ControlSystemOperate(models.Model):

    plc_code = ''

    _name = 'control.system.operate'
    _description = 'control system operate'
    workshop = fields.Char(string="车间代号")
    line = fields.Char(string="线体代号")
    machine = fields.Char(string="机台代号")
    emergency_stop = fields.Boolean(string="紧急停止")
    manual_control = fields.Boolean(string="手动控制")
    auto_control = fields.Boolean(string="自动控制")
    stop = fields.Boolean(string="停止")
    pause = fields.Boolean(string="暂停")
    reset = fields.Boolean(string="复位")
    source_target = fields.Integer(string="源目标")
    new_target = fields.Integer(string="新目标")
    status = fields.Selection([
        ('idle', '空闲'),
        ('running', '运行中'),
        ('paused', '暂停'),
        ('stopped', '停止'),
        ('emergency', '紧急停止')
    ], string="状态", default='idle')
    # storage_info = fields.Many2one('automatic.storage.location', string='库位信息')
    # stacker = fields.Many2one('warehouse.information', string="堆高机信息")
    # entrance1 = fields.Many2one('warehouse.information', string="入口1信息")
    # entrance2 = fields.Many2one('warehouse.information', string="入口2信息")

    # 展示框号
    show_storage_pack_number = fields.Integer(string='框号')

    storage_goods_status = fields.Boolean(string='库位有货')
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


    # def __init__(self, env: api.Environment, ids: tuple[IdType, ...], prefetch_ids: Reversible[IdType]):
    #     super().__init__(env, ids, prefetch_ids)
    #     self.goods_status = None

    def _get_cron_record(self):
        """获取或创建定时任务记录"""
        cron = self.env.ref('plc_interface.plc_sync_cron', raise_if_not_found=False)
        if not cron:
            cron = self.env['ir.cron'].create({
                'name': 'PLC数据自动同步',
                'model_id': self.env.ref('plc_interface.model_plc_interface').id,
                'state': 'code',
                'code': 'model._cron_sync_plc_data()',
                'interval_number': self.cron_interval,
                'interval_type': 'minutes',
                'active': self.cron_active
            })
            self.env['ir.model.data'].create({
                'name': 'plc_sync_cron',
                'module': 'plc_interface',
                'model': 'ir.cron',
                'res_id': cron.id,
            })
        return cron

    @api.model
    def connect_plc(self, ip='192.168.0.10', rack=0, slot=1, retries=3, retry_interval=5) -> snap7.client.Client:
        """
        连接西门子PLC并返回客户端对象
        :param ip: PLC的IP地址
        :param rack: 机架号（默认0）
        :param slot: 插槽号（默认1，适用于S7-1200/1500）
        :param retries: 最大重试次数
        :param retry_interval: 重试间隔（秒）
        :return: 成功返回client对象，失败返回None
        """
        client = snap7.client.Client()
        for attempt in range(1, retries + 1):
            try:
                logging.info(f"尝试连接PLC ({ip}) 第{attempt}/{retries}次...")
                client.connect(ip, rack, slot)
                if client.get_connected():
                    logging.info("连接成功!")
                    return client
            except Exception as e:
                logging.error(f"连接失败: {str(e)}")
                if attempt < retries:
                    logging.error(f"{retry_interval}秒后重试...")
                    time.sleep(retry_interval)
        return None

    @api.model
    def batch_read_plc(self, point):
        """
        通用数据读取方法
        :param data_points: plc.data.point 记录集
        :return: 字典格式结果 {数据点ID: 值}
        """
        logging.info(point)
        client = self.connect_plc()
        if not client:
            return None
        try:
            # 根据类型读取数据
            if point['data_type'] == 'int':
                # 读取 16 位整数
                raw = client.db_read(
                    db_number=point['db_number'],
                    start=point['address'],
                    size=2  # 2 bytes for int16
                )
                value = struct.unpack('>h', raw)[0]
            elif point['data_type'] == 'float':
                # 读取 32 位浮点数
                raw = client.db_read(
                    db_number=point['db_number'],
                    start=point['address'],
                    size=4  # 4 bytes for float
                )
                value = struct.unpack('>f', raw)[0]
            elif point['data_type'] == 'bool':
                # 读取布尔值（1字节）
                raw = client.db_read(
                    db_number=point['db_number'],
                    start=point['address'],
                    size=1  # 1 byte
                )
                byte_val = raw[0]
                bit_offset = point['bit_offset']
                value = bool(byte_val & (1 << bit_offset))
            elif point['data_type'] == 'str':
                # 读取字符串（固定长度）
                str_length = point['str_length']
                raw = client.db_read(
                    db_number=point['db_number'],
                    start=point['address'],
                    size=str_length
                )
                max_len = struct.unpack('>H', raw[0:2])[0]  # 前2字节：最大长度
                actual_len = struct.unpack('>H', raw[2:4])[0]  # 后2字节：实际长度
                value = raw[4:4 + actual_len].decode('utf-8', errors='ignore').strip('\x00')
            else:
                logging.info(f"不支持的数据类型: {point['data_type']}")
                value = None
        except Exception as e:
            logging.error(f"读取数据失败: {str(e)}")
            return value
        # finally:
        #     if client.get_connected():
        #         client.disconnect()
        return value


    @api.model
    def batch_to_plc(self, area: 'DB', value: bool,db_number=202, address: int = 0, bit_offset: int = -1, data_type: str = 'byte',  str_length: int = 20,  ) -> bool:
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
        client = self.connect_plc()
        if client is None:
            raise ConnectionError("PLC连接失败")
        if area not in ['DB']:
            raise ValueError("区域参数错误，只支持 'DB'")
        if area == 'DB' and db_number == 0:
            raise ValueError("写入DB块时必须明确指定db_number参数！")
        if data_type == 'bool':
            if bit_offset == -1:
                raise ValueError("布尔类型必须指定 bit_offset (0-7)")
            if not (0 <= bit_offset <= 7):
                raise ValueError("bit_offset 必须在 0-7 范围内")
            if not isinstance(value, bool):
                raise TypeError("布尔类型的值必须是 True/False")
        try:
            # 以下执行写入
            if data_type == 'bool':
                if area == 'DB':
                    current_data = client.db_read(db_number, address, 1)
                    current_byte = current_data[0]
                    # 修改特定位
                    if value:
                        new_byte = current_byte | (1 << bit_offset)
                    else:
                        new_byte = current_byte & ~(1 << bit_offset)
                    data_to_write = bytearray([new_byte])
                    # 整数类型（16位）
            elif data_type == 'int':
                if not isinstance(value, int):
                    raise TypeError("int类型需要整数值")
                data_to_write = bytearray(struct.pack('>h', value))  # 大端16位
            # 浮点类型（32位）
            elif data_type == 'float':
                if not isinstance(value, (int, float)):
                    raise TypeError("float类型需要数值")
                if address % 4 != 0:
                    raise ValueError("浮点数地址必须是4的倍数（如DB1.DBD0）")
                data_to_write = bytearray(struct.pack('>f', value))
            # 字符串类型（西门子格式）
            elif data_type == 'str':
                if not isinstance(value, str):
                    raise TypeError("str类型需要字符串值")
                if str_length < len(value):
                    raise ValueError("字符串长度超过定义长度")
                encoded_str = value.encode('utf-8')
                data_to_write = bytearray(struct.pack(
                    f'>BB{str_length}s',  # 格式：最大长度(2字节) + 实际长度(2字节) + 内容
                    str_length,
                    len(encoded_str),
                    encoded_str.ljust(str_length, b'\x00')
                ))
            # 原始字节类型
            elif data_type == 'byte':
                if isinstance(value, (bytes, bytearray)):
                    data_to_write = bytearray(value)
                else:
                    data_to_write = bytearray([value])
            else:
                raise ValueError(f"不支持的数据类型: {data_type}")

            if area == 'DB':
                client.db_write(db_number, address, data_to_write)
            logging.info( f"写入成功：{area}{f'.DB{db_number}' if area == 'DB' else ''}[{address}.{bit_offset if data_type == 'bool' else ''}] = {value}")
            return True
        except Exception as e:
            logging.error(f"写入数据失败: {str(e)}")
            return False
        # finally:
        #     if client.get_connected():
        #         client.disconnect()

    def update_plc(self):
        """传递到PLC"""
        # 库位有货
        read_storage_goods_status = self.storage_goods_status
        code = {
            'value' : read_storage_goods_status,
            'address': 0,
            'data_type' : 'bool'
        }

        # 取消库位
        read_storage_goods_cancel = self.storage_goods_cancel
        code = {
            'value': read_storage_goods_status,
            'address': 2,
            'data_type': 'bool'
        }
        # 框号
        read_storage_pack_number = self.storage_pack_number
        code = {
            'value': read_storage_goods_status,
            'address': 2,
            'data_type': 'bool'
        }
        # 库位编号
        read_storage_base_number = self.storage_base_number
        code = {
            'value': read_storage_goods_status,
            'address': 2,
            'data_type': 'bool'
        }
        # 库位号
        read_storage_location_number = self.storage_location_number
        code = {
            'value': read_storage_goods_status,
            'address': 2,
            'data_type': 'bool'
        }
        # 框条码
        read_storage_pack_barcode = self.storage_pack_barcode
        code = {
            'value': read_storage_goods_status,
            'address': 2,
            'data_type': 'bool'
        }
        base_date = self.storage_base_number
        plc_interface = self.connect_plc()
        if not plc_interface:
            pass
        logging.info(self.storage_goods_status)
        trs = [
            {
                'area': 'DB',
                'db_number': 202,
                'address': 2,
                'data_type': 'int'
            },
            {
                'area': 'DB',
                'db_number': 202,
                'address': 2,
                'data_type': 'bool'
            }
        ]
        # 写入调用
        code = self.batch_to_plc(
            area='DB',
            value=base_date,
            db_number=202,
            address=2,
            data_type='int'
        )
        # 对某个DB内进行批量写入



    def fetch_plc(self):
        """读取plc"""

        value = self.batch_read_plc({
            'id': 'temp_sensor',
            'name': 'PLC_1',
            'area': 'DB',
            'db_number': 202,
            'address': 2,
            'bit_pos': 0,
            'str_len': 20,
            'data_type': 'int'
        })
        for result in self:
            result.show_storage_pack_number = value




    def emergency_button(self):
        for record in self:
            record.emergency_stop = not record.emergency_stop

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

    # def action_button(self):
    #     if self.emergency_stop:
    #         self.emergency_stop = False
    #     else:
    #         self.emergency_stop = True


    # def example_usage(self):
    #     ip = '192.168.0.10'
    #     rack = 0
    #     slot = 1
    #     db_number = 202
    #     start = 2
    #     size = 1
    #
    #     # 读取数据
    #     # data = self.env['communication.property'].read_plc_data(ip, rack, slot, db_number, start, size)
    #     data = self.read_plc_data(ip, rack, slot, db_number, start, size)
    #     print(f"读取的数据: {data}")


#----------------------------------------------------------------------------
#Hugo 25.05.08

    @api.model
    def inventory_information_write(self,bits0,bits1, value1,value2,value3,value4,
                                    db_number: int = 0,address: int = 0,  str_length: int = 20,
                                    rack: int = 0,   slot: int = 1 ) -> bool:
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

        # data_to_write1:int

        # if not hasattr(self, 'plc_client') or not self.plc_client.get_connected():
        #     self.plc_client = self.connect_plc()
        # else:
        #     client = self.plc_client
        # if client is None:
        #     raise ConnectionError("PLC连接失败")
        client = self.connect_plc()
        if not client:
            pass
        try:
            # 写入一个字节位
            # if len(bits) != 8:
            #     raise ValueError("必须提供8个布尔值")
            # byte = 0
            # for i in range(8):
            #     if bits[i]:
            #         byte |= (1 << (7 - i))
            # data_to_write = bytearray([byte])

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

          # finally:
    #    if client.get_connected():
    #       client.disconnect()

    def write_storage_information(self):
        plc_interface = self.connect_plc()
        if not plc_interface:
            pass
        code = self.inventory_information_write(
            db_number=202,
            address=0,
            bits0=self.storage_goods_status,
            bits1=self.storage_goods_cancel,
            value1=self.storage_pack_number,
            value2=self.storage_base_number,
            value3=self.storage_location_number,
            value4=self.storage_pack_barcode,
        )

    def write_stacker_information(self):
        plc_interface = self.connect_plc()
        if not plc_interface:
            pass
        print(self.stacker_pack_number)
        code = self.inventory_information_write(
            db_number=202,
            address=36,
            bits0=self.stacker_goods_status,
            bits1=self.stacker_goods_cancel,
            value1=self.stacker_pack_number,
            value2=self.stacker_base_number,
            value3=self.stacker_location_number,
            value4=self.stacker_pack_barcode,
        )

    def write_entrance1_information(self):
        plc_interface = self.connect_plc()
        if not plc_interface:
            pass
        code = self.inventory_information_write(
            db_number=202,
            address=72,
            bits0=self.entrance1_goods_status,
            bits1=self.entrance1_goods_cancel,
            value1=self.entrance1_pack_number,
            value2=self.entrance1_base_number,
            value3=self.entrance1_location_number,
            value4=self.entrance1_pack_barcode,
        )

    def write_entrance2_information(self):
        plc_interface = self.connect_plc()
        if not plc_interface:
            pass
        code = self.inventory_information_write(
            db_number=202,
            address=108,
            bits0=self.entrance2_goods_status,
            bits1=self.entrance2_goods_cancel,
            value1=self.entrance2_pack_number,
            value2=self.entrance2_base_number,
            value3=self.entrance2_location_number,
            value4=self.entrance2_pack_barcode,
        )


    @api.model
    def inventory_information_read(self,
                                    db_number: int = 0,address: int = 0,  str_length: int = 20,
                                    rack: int = 0,   slot: int = 1 ) -> bool:
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

        # data_to_write1:int

        # if not hasattr(self, 'plc_client') or not self.plc_client.get_connected():
        #     self.plc_client = self.connect_plc()
        # else:
        #     client = self.plc_client
        # if client is None:
        #     raise ConnectionError("PLC连接失败")

        client = snap7.client.Client()
        try:
            # 写入一个字节位
            # if len(bits) != 8:
            #     raise ValueError("必须提供8个布尔值")
            # byte = 0
            # for i in range(8):
            #     if bits[i]:
            #         byte |= (1 << (7 - i))
            # data_to_write = bytearray([byte])

            current_data = client.db_read(db_number, address, 1)
            current_byte = current_data[0]
            bit0 = bool(current_byte & (1 << 0))  # 获取第 0 位的状态

            bit1 = bool(current_byte & (1 << 1))  # 获取第 1 位的状态


            raw_data = client.db_read(db_number, address + 2, 2)
            value1 = struct.unpack('>h', raw_data)[0]
            # self.write({'value1': value1})
            raw_data = client.db_read(db_number, address + 4, 2)
            value2 = struct.unpack('>h', raw_data)[0]

            raw_data = client.db_read(db_number, address + 10, 4)
            value3 = struct.unpack('>I', raw_data)[0]

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

            raw_data = client.db_read(db_number, address + 14, str_length)
            value4 = raw_data[2:2 + raw_data[1]].decode('utf-8').strip('\x00')
            print(value4)
            #return {value3, 123, }
            # return True
            return {
                "bit0":bit0,
                'bit1': bit1,
                'value1': value1,
                'value2': value2,
                'value3': value3,
                'value4': value4,
            }

        except Exception as e:
            return False
        #
        # finally:
        #    if client.get_connected():
        #       client.disconnect()

    def read_storage_information(self):
        plc_interface = self.connect_plc()
        if not plc_interface:
            pass
        code = self.inventory_information_read(
            db_number=202,
            address=0,
        )
        logging.info(code)
        # for result in self:
        #     # result.storage_goods_status = code.get('bit0')
        #     result.storage_pack_number = code.get('value1')
        #     result.storage_base_number = code.get('value2')
        #     result.storage_location_number = code.get('value3')
        #     result.storage_pack_barcode = code.get('value4')
        # print(value)

    def read_stacker_information(self):
        plc_interface = self.connect_plc()
        if not plc_interface:
            pass
        code = self.inventory_information_read(
            db_number=202,
            address=36,
        )
        logging.info(code)
        # for result in self:
        #     result.stacker_goods_status = code.get('bit0')
        #     result.stacker_pack_number = code.get('value1')
        #     result.stacker_base_number = code.get('value2')
        #     result.stacker_location_number = code.get('value3')
        #     result.stacker_pack_barcode = code.get('value4')

    def read_entrance1_information(self):
        plc_interface = self.connect_plc()
        if not plc_interface:
            pass
        code = self.inventory_information_read(
            db_number=202,
            address=72,
        )
        logging.info(code)
        # for result in self:
        #     result.entrance1_goods_status = code.get('bit0')
        #     result.entrance1_pack_number = code.get('value1')
        #     result.entrance1_base_number = code.get('value2')
        #     result.entrance1_location_number = code.get('value3')
        #     result.entrance1_pack_barcode = code.get('value4')

    def read_entrance2_information(self):
        plc_interface = self.connect_plc()
        if not plc_interface:
            pass
        code = self.inventory_information_read(
            db_number=202,
            address=108,
        )
        logging.info(code)
        # for result in self:
        #     result.entrance2_goods_status = code.get('bit0')
        #     result.entrance2_pack_number = code.get('value1')
        #     result.entrance2_base_number = code.get('value2')
        #     result.entrance2_location_number = code.get('value3')
        #     result.entrance2_pack_barcode = code.get('value4')


#25.05.14 hugo

    # def __init__(self, *args, **kwargs):
    #     super(ControlSystemOperate, self).__init__(*args, **kwargs)
    #     self.scheduler = None
    def read_text_plc(self):
        # client = snap7.client.Client()
        # client.connect('192.168.0.10', 0, 1)
        # raw_data = client.db_read(202,  4, 2)
        # value2 = struct.unpack('>h', raw_data)[0]
        # logging.info(f'value2: {value2}')
        print('Test')

    def start_plc_scheduler(self):
        """启动定时任务"""
        # self.scheduler = BackgroundScheduler()
        # self.scheduler.add_job(
        #     self.read_write_plc_data,
        #     'interval',
        #     milliseconds=500,
        #     id='plc_io_job'
        # )
        scheduler = BackgroundScheduler()
        if 'plc_io_job' in [job.id for job in scheduler.get_jobs()]:
            scheduler.remove_job('plc_io_job')
        scheduler.add_job(
            self.read_write_plc_data,
            'interval',
            seconds=1,  # 或者使用 milliseconds=500 但需注意：某些调度器不支持毫秒
            id='plc_io_job'
        )
        scheduler.start()
        _logger.info("PLC定时任务已启动，间隔500ms")



    def read_write_plc_data(self):
        """定时执行PLC读写逻辑"""
        try:
            _logger.info("开始执行PLC读写操作...")

            # 示例：读取库位信息
            self.read_storage_information()

            # 示例：写入堆垛机信息
            self.write_stacker_information()

            # 可根据需要继续添加更多 read/write 方法

        except Exception as e:

            _logger.error(f"PLC通信失败: {str(e)}")

    @api.model
    def run_at_startup(self):
        """Odoo启动时调用的方法"""
        thread = threading.Thread(target=self.start_plc_scheduler, daemon=True)
        thread.start()
        _logger.info("PLC后台线程已启动")
        # except Exception as e:
        # print(f"Failed to start thread: {e}")

    # @api.model_cr
    def initialize_data(self):
        # env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        # control_model = env['control.system.operate']
        self.run_at_startup()
    #     pass

# control_system_operate.py 最上方定义