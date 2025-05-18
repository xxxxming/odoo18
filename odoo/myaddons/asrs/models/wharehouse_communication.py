# -*- coding: utf-8 -*-

import snap7
from snap7.util import *
# from snap7.snap7exceptions import Snap7Exception
from odoo import models, fields, api

# import time
# from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
# from odoo import api, registry, SUPERUSER_ID
import logging

class CommunicationProperty(models.Model):
    _name = 'communication.property'
    _description = 'communication property'
    name = fields.Char(string='名称')
    ip = fields.Char(string='IP地址')
    rack = fields.Integer(string='机架')
    slot = fields.Integer(string='插槽')

def connect_to_plc(self, ip, rack, slot):

    plc = snap7.client.Client()
    try:
        plc.connect(self, ip, rack, slot)
        return plc
    except Snap7Exception as e:
        self.env.cr.rollback()
        self.env.invalidate_all()
        raise Exception(f"无法连接到PLC: {e}")

@api.model
def read_plc_data(self, ip, rack, slot, db_number, start, size):

    plc = self.connect_to_plc(ip, rack, slot)
    try:
        data = plc.db_read(db_number, start, size)
        return data
    except Snap7Exception as e:
        self.env.cr.rollback()
        self.env.invalidate_all()
        raise Exception(f"读取PLC数据时出错: {e}")
    finally:
        plc.disconnect()


def write_plc_data(self, ip, rack, slot, db_number, start, data):

    plc = self.connect_to_plc(ip, rack, slot)
    try:
        plc.db_write(db_number, start, data)
    except Snap7Exception as e:
        self.env.cr.rollback()
        self.env.invalidate_all()
        raise Exception(f"写入PLC数据时出错: {e}")
    finally:
        plc.disconnect()


def example_usage(self):
    """
    示例用法：读取和写入PLC数据
    """
    ip = '192.168.0.10'  # 替换为你的PLC IP地址
    rack = 0  # 替换为你的PLC机架号
    slot = 1  # 替换为你的PLC插槽号
    db_number = 202  # 替换为你的数据块号
    start = 0  # 替换为起始地址
    size = 1  # 替换为读取的字节数

    # 读取数据
    data = self.read_plc_data(ip, rack, sWin200lot, db_number, start, size)
    print(f"读取的数据: {data}")

    # 写入数据
    new_data = bytearray([1])  # 替换为你想要写入的数据
    self.write_plc_data(ip, rack, slot, db_number, start, new_data)
    print("数据已写入PLC")


class PLCInterface(models.Model):
    _name = 'plc.interface'
    _description = 'PLC Communication Interface'


    name = fields.Char(string='名称')
    ip = fields.Char(string='IP地址')
    rack = fields.Integer(string='机架')
    slot = fields.Integer(string='插槽')

    cron_interval = fields.Integer(
        string='同步间隔(分钟)',
        default=5,
        help="数据同步频率（单位：分钟）"
    )
    cron_active = fields.Boolean(
        string='启用定时同步',
        default=True
    )

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
                print(f"尝试连接PLC ({ip}) 第{attempt}/{retries}次...")
                client.connect(ip, rack, slot)
                if client.get_connected():
                    logging.info("连接成功!")
                    return client
            except Exception as e:
                print(f"连接失败: {str(e)}")
                if attempt < retries:
                    logging.error(f"{retry_interval}秒后重试...")
                    time.sleep(retry_interval)
        return None

    @api.model
    def batch_read_plc(self, plc_ip: str, requests, rack: int = 0, slot: int = 1):
        """
        批量读取PLC数据（支持字符串、整数、浮点、布尔值）
        :param plc_ip: PLC的IP地址
        :param requests: 读取请求列表，每个请求格式为：
            {
                'area': 'DB'/'M'/'Q',  # 必填
                'db_number': int,       # DB块号（仅area='DB'时必填）
                'address': int,         # 起始地址（字节）
                'data_type': 'str'/'int'/'float'/'bool'/'byte',
                'count': int,          # 元素个数（布尔时为位数，字符串时为总长度）
            }
        :param rack: 机架号
        :param slot: 插槽号
        :return: 结果列表，每个元素格式为：
            {
                'success': bool,
                'value': Union[str, int, float, bool, bytes],
                'error': str
            }
        """
        client = connect_plc()
        if client is None:
            raise ConnectionError("PLC连接失败")
        results = []
        try:
            for req in requests:
                result = {'success': False, 'value': None, 'error': ''}
                try:
                    area = req['area']
                    address = req['address']
                    data_type = req['data_type']
                    count = req.get('count', 1)
                    db_number = req.get('db_number', 0)
                    # 根据数据类型计算读取参数
                    if data_type == 'bool':
                        # 布尔类型：读取字节后解析指定位
                        byte_data = client.db_read(db_number, address, 1) if area == 'DB' else \
                            client.mb_read(address, 1) if area == 'M' else \
                                client.ab_read(address, 1)
                        bit_offset = req.get('bit_offset', 0)
                        if bit_offset < 0 or bit_offset > 7:
                            raise ValueError("位偏移必须为0-7")
                        result['value'] = bool(byte_data[0] & (1 << bit_offset))
                    elif data_type == 'str':
                        # 字符串类型：读取指定长度并解析
                        str_length = count  # 总长度（含头部4字节）
                        raw_data = client.db_read(db_number, address, str_length)
                        max_len = struct.unpack('>H', raw_data[0:2])[0]
                        actual_len = struct.unpack('>H', raw_data[2:4])[0]
                        result['value'] = raw_data[4:4 + actual_len].decode('utf-8').strip('\x00')
                    elif data_type in ['int', 'float', 'byte']:
                        # 计算需要读取的字节数
                        bytes_to_read = {
                            'int': 2 * count,
                            'float': 4 * count,
                            'byte': count
                        }[data_type]

                        # 读取原始数据
                        raw_data = client.db_read(db_number, address, bytes_to_read) if area == 'DB' else \
                            client.mb_read(address, bytes_to_read) if area == 'M' else \
                                client.ab_read(address, bytes_to_read)
                        # 解析数据
                        if data_type == 'int':
                            result['value'] = [struct.unpack('>h', raw_data[i * 2:(i + 1) * 2])[0] for i in
                                               range(count)]
                        elif data_type == 'float':
                            result['value'] = [struct.unpack('>f', raw_data[i * 4:(i + 1) * 4])[0] for i in
                                               range(count)]
                        else:
                            result['value'] = bytes(raw_data)
                    else:
                        raise ValueError(f"不支持的数据类型: {data_type}")
                    result['success'] = True
                except Exception as e:
                    result['error'] = f"{type(e).__name__}: {str(e)}"
                results.append(result)
        except Exception as e:
            # 全局错误处理（如连接失败）
            results.append({'success': False, 'value': None, 'error': str(e)})
        finally:
            if client.get_connected():
                client.disconnect()
        return results

    @api.model
    def batch_to_plc(self, plc_ip: str,
                     area: str,  # 区域: 'DB', 'M', 'Q'
                     value: bool,
                     db_number: int = 0,  # DB块号（必须明确指定！）
                     address: int = 0,  # 字节地址
                     bit_offset: int = -1,  # 位偏移（0-7，仅布尔类型需要）
                     data_type: str = 'byte',  # 数据类型: bool/int/float/str/byte
                     str_length: int = 20,  # 字符串总长度（仅字符串类型需要）
                     rack: int = 0,  # 默认机架号
                     slot: int = 1  # 默认插槽号
                     ) -> bool:
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
        client = connect_plc()
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

                    # --------------------------
                    # 数据写入（必须传递 bytearray）
                    # --------------------------
                if area == 'DB':
                    client.db_write(db_number, address, data_to_write)
                elif area == 'M':
                    client.mb_write(address, data_to_write)
                elif area == 'Q':
                    client.ab_write(address, data_to_write)

                print(
                    f"写入成功：{area}{f'.DB{db_number}' if area == 'DB' else ''}[{address}.{bit_offset if data_type == 'bool' else ''}] = {value}")
                return True

        except Exception as e:
            return False
        finally:
            if client.get_connected():
                client.disconnect()





#----------------------------------------------------------------------------
#Hugo 25.05.12

# _logger = logging.getLogger(__name__)
#
# class PLCTaskManager:
#     def __init__(self, env):
#         self.env = env
#         self.scheduler = None
#         self.running = False
#
#     def start_thread(self):
#         if not self.running:
#             thread = threading.Thread(target=self._run_scheduler, name="PLC_Scheduler_Thread")
#             thread.daemon = True
#             thread.start()
#             self.running = True
#             _logger.info("PLC定时任务线程已启动")
#
#     def stop_thread(self):
#         if self.scheduler:
#             self.scheduler.shutdown()
#         self.running = False
#         _logger.info("PLC定时任务线程已停止")
#
#     def _run_scheduler(self):
#         with api.Environment.manage():
#             new_cr = registry(self.env.cr.dbname).cursor()
#             env = api.Environment(new_cr, SUPERUSER_ID, {})
#
#             try:
#                 self.scheduler = BackgroundScheduler()
#                 self.scheduler.add_job(
#                     self._read_write_plc_data,
#                     'interval',
#                     milliseconds=500,
#                     id='plc_500ms_task'
#                 )
#                 self.scheduler.start()
#                 _logger.info("PLC每500ms任务已启动")
#
#                 # 防止线程退出
#                 while self.running:
#                     time.sleep(1)
#             except Exception as e:
#                 _logger.error(f"调度器异常: {e}")
#             finally:
#                 new_cr.close()
#
#     def _read_write_plc_data(self):
#         """每500ms执行一次的PLC读写逻辑"""
#         _logger.info("开始执行PLC读写任务...")
#
#         try:
#             # 调用你定义的 read_plc_data 或 batch_read_plc 方法
#             plc_interface = self.env['plc.interface']
#             ip = "192.168.0.10"
#             rack = 0
#             slot = 1
#             db_number = 202
#             start = 2
#             size = 1
#
#             data = plc_interface.read_plc_data(ip, rack, slot, db_number, start, size)
#             _logger.info(f"读取到数据: {data}")
#
#             # 示例写入
#             write_data = bytearray([123])
#             plc_interface.write_plc_data(ip, rack, slot, db_number, start, write_data)
#             _logger.info("数据已写入PLC")
#
#         except Exception as e:
#             _logger.error(f"执行PLC任务失败: {e}")





































































































