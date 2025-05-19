# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
import threading
import struct
from apscheduler.schedulers.background import BackgroundScheduler
from .plc_connect import PlcClient
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

    def batch_read_plc(self, row_data):
        """
        通用数据读取方法
        :param row_data: plc.data 记录集
        :return: value 读取结果
        """
        value = PlcClient().read(row_data)
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
        PlcClient().write(data)
        # 取消库位
        read_storage_goods_cancel = self.storage_goods_cancel
        if read_storage_goods_cancel == None:
            read_storage_goods_cancel = False
        data = {
            'value': read_storage_goods_cancel,
            'bit_index': 2,
            'value_type': 'bool'
        }
        PlcClient().write(data)
        # 框号
        read_storage_pack_number = self.storage_pack_number
        data = {
            'value': read_storage_pack_number,
            'offset': 2,
            'value_type': 'int'
        }
        PlcClient().write(data)
        # 库位编号
        read_storage_base_number = self.storage_base_number
        data = {
            'value': read_storage_base_number,
            'offset': 4,
            'value_type': 'int'
        }
        PlcClient().write(data)
        # 库位号
        read_storage_location_number = self.storage_location_number
        data = {
            'value': read_storage_location_number,
            'offset': 6,
            'value_type': 'int'
        }
        PlcClient().write(data)
        # 框条码
        stacker_pack_barcode = self.stacker_pack_barcode
        data = {
            'value': stacker_pack_barcode,
            'offset': 14,
            "string_max_len": 8,
            'value_type': 'string'
        }
        PlcClient().write(data)
        # 对某个DB内进行批量写入

    def read_write_plc_data(self):
        if plc_lock.locked():
            _logger.info("上一次任务未完成，本次跳过")
            return None
        with plc_lock:
            results = [
                # 库位有货
                {'offset': 0, 'value_type': 'bool', 'bit_index': 0},
                # 框号
                {'offset': 2, 'value_type': 'int'},
                # 库位编号
                {'offset': 3, 'value_type': 'int'},
                # 库位号
                {'offset': 4, 'value_type': 'int'},
                # 框条码
                {'offset': 5, 'value_type': 'int'},
            ]
            for result in results:
                self.batch_read_plc(result)












    def start_plc_scheduler(self):
        """启动定时任务"""
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            self.read_write_plc_data,
            'interval',
            max_instances=2, #允许同时最多跑 2 个
            seconds=0.2,
        )
        scheduler.start()

    def initialize_data(self):
        """
        hook调用
        """
        thread = threading.Thread(target=self.start_plc_scheduler(), daemon=True)
        thread.start()
        _logger.info("PLC后台线程已启动")


    def fetch_plc(self):
        """读取测试-批量"""
        # 读取库位信息例子
        results = [
            # 库位有货
            {'offset': 0, 'value_type': 'bool', 'bit_index':0},
            # 框号
            { 'offset': 2, 'value_type': 'int'},
            # 库位编号
            {'offset': 3, 'value_type': 'int'},
            # 库位号
            {'offset': 4, 'value_type': 'int'},
            # 框条码
            {'offset': 5, 'value_type': 'int'},
        ]
        for result in results:
            value = self.batch_read_plc(result)

    def emergency_button(self):
        for record in self:
            _logger.info(record.emergency_stop)
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
            # return {value3, 123, }
            # return True
            return {
                "bit0": bit0,
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

    # 25.05.14 hugo

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


