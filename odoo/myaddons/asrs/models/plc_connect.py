import snap7
import logging
import time
import snap7
from snap7.util import *
from snap7.util import get_int, set_int, get_bool, set_bool, get_string, set_string
from snap7.util import (
    set_int, get_int,
    set_bool, get_bool,
    set_string, get_string
)
_logger = logging.getLogger(__name__)


class PlcClient:

    _client = None

    def __init__(self):
        self.ip = '192.168.0.10'
        self.rack = 0
        self.slot = 1
        #self.db_number = 202
        if PlcClient._client is None:
            PlcClient._client = snap7.client.Client()
        self.client = PlcClient._client


    def connect_plc(self) -> snap7.client.Client:
        """
        连接西门子PLC并返回客户端对象
        : retries: 最大重试次数
        : retry_interval: 重试间隔（秒）
        :return: 成功返回client对象，失败返回None
        """
        retries = 3
        retry_interval = 5
        for attempt in range(1, retries + 1):
            try:
                self.client.connect(self.ip, self.rack, self.slot)
                if  self.client.get_connected():
                    _logger.info("PLC连接成功!")
                    return  self.client
            except Exception as e:
                _logger.error(f"\n连接失败: {str(e)}\n")
                if attempt < retries:
                    _logger.error(f"{retry_interval}秒后重试...")
                    time.sleep(retry_interval)
        return None

    def is_connected(self) -> bool:
        """
        检查PLC连接状态
        :return: 返回当前PLC的连接状态（True表示已连接，False表示未连接）
        """
        return self.client.get_connected()

    def disconnect(self):
        self.client.disconnect()
        _logger.info("已断开PLC连接")

    def set_db_number_write(self, row_data):
        """
        写入数据到PLC，自动判断类型。 方案1:用传递db_number
        参数：
        - offset: 起始偏移地址（字节）
        - value: 要写入的值
        - value_type: 类型字符串：'int'、'bool'、'string'
        - bit_index: 若为bool，指定字节内位索引（0~7）
        - string_max_len: 若为string，最大长度（如 STRING[20] => 20）
        """
        db_number = row_data.get('db_number')
        if db_number is None:
            raise ValueError("db_number 不能为空")
        value = row_data.get('value')
        offset = row_data.get('start_address')
        value_type = row_data.get('value_type')
        bit_index = row_data.get('bit_index')
        string_max_len = row_data.get('string_max_len')

        #读取 自动判断是否连接. 否则尝试重连
        if not self.client.get_connected():
            self.connect_plc()
        if value_type == 'int':
            if not isinstance(value, int) or not (-32768 <= value <= 32767):
                raise ValueError("INT值必须是 -32768 到 32767 之间的整数")
            data = bytearray(2)
            set_int(data, 0, value)
            self.client.db_write(db_number, offset, data)
            _logger.info(f"写入 INT: {value} 到 DB{db_number}, 偏移 {offset}")

        elif value_type == 'bool':
            if not isinstance(value, bool):
                raise ValueError("BOOL值必须是 True 或 False")
            if bit_index is None or not (0 <= bit_index <= 7):
                raise ValueError("bit_index 必须提供并在 0~7 之间")
            data = self.client.db_read(db_number, offset, 1)
            set_bool(data, 0, bit_index, value)
            self.client.db_write(db_number, offset, data)
            _logger.info(f"写入 BOOL: {value} 到 DB{db_number}, 字节 {offset}, 位 {bit_index}")

        elif value_type == 'string':
            if not isinstance(value, str):
                raise ValueError("传值必须是字符串")
            if string_max_len is None:
                raise ValueError("string_max_len 必须指定")
            if len(value) > string_max_len:
                raise ValueError(f"字符串长度不能超过 {string_max_len}")
            data = bytearray(string_max_len + 2)
            set_string(data, 0, value, string_max_len)
            self.client.db_write(db_number, offset, data)
            _logger.info(f"写入 STRING: '{value}' 到 DB{db_number}, 偏移 {offset}")

        else:
            raise ValueError(f"不支持的类型: {value_type}")

    def set_db_number_read(self, row_data):
        """
        方案1:用传递db_number
        用于从PLC的DB块中读取不同类型的数据，根据value_type参数决定读取的数据类型，并调用相应的解析函数返回结果
        """
        if not self.client.get_connected():
            self.connect_plc()

        db_number = row_data.get('db_number')
        if db_number is None:
            raise ValueError("db_number 不能为空")
        offset = row_data.get('offset')
        value_type = row_data.get('value_type')
        bit_index = row_data.get('bit_index')
        string_max_len = row_data.get('string_max_len')

        if value_type == 'int':
            data = self.client.db_read(db_number, offset, 2)
            return get_int(data, 0)

        elif value_type == 'bool':
            if bit_index is None or not (0 <= bit_index <= 7):
                raise ValueError("bit_index 必须在 0~7 范围内")
            data = self.client.db_read(db_number, offset, 1)
            return get_bool(data, 0, bit_index)

        elif value_type == 'string':
            if string_max_len is None:
                raise ValueError("读取字符串时必须提供 string_max_len")
            data = self.client.db_read(db_number, offset, string_max_len + 2)
            return get_string(data, 0, string_max_len)
        else:
            raise ValueError(f"不支持的数据类型: {value_type}")

    # 位置偏移量 #
    def read_by_offset(self, row_data):
        """
        根据 row_data 中的 db_number、offset 和 value_type 从 PLC 的 DB 中按偏移量读取数据。
        支持类型：int、bool、string
        """
        if not self.client.get_connected():
            self.connect_plc()

        db_number = row_data.get('db_number')
        offset = row_data.get('offset')
        value_type = row_data.get('value_type')
        bit_index = row_data.get('bit_index')  # 仅 bool 类型需要
        string_max_len = row_data.get('string_max_len')  # 仅 string 类型需要

        if db_number is None or offset is None or value_type is None:
            raise ValueError("必须提供 db_number、offset 和 value_type")

        if value_type == 'int':
            data = self.client.db_read(db_number, offset, 2)
            return get_int(data, 0)

        elif value_type == 'bool':
            if bit_index is None or not (0 <= bit_index <= 7):
                raise ValueError("bool 类型必须提供 bit_index (0~7)")
            data = self.client.db_read(db_number, offset, 1)
            return get_bool(data, 0, bit_index)

        elif value_type == 'string':
            if string_max_len is None:
                raise ValueError("string 类型必须提供 string_max_len")
            data = self.client.db_read(db_number, offset, string_max_len + 2)
            return get_string(data, 0, string_max_len)

        else:
            raise ValueError(f"不支持的 value_type: {value_type}")

    def write_by_offset(self, row_data):
        """
        根据 row_data 中的 db_number、offset 和 value_type 向 PLC 的 DB 中按偏移量写入数据。
        支持类型：int、bool、string
        """
        if not self.client.get_connected():
            self.connect_plc()

        db_number = row_data.get('db_number')
        offset = row_data.get('offset')
        value_type = row_data.get('value_type')
        value = row_data.get('value')
        bit_index = row_data.get('bit_index')  # 仅 bool 类型需要
        string_max_len = row_data.get('string_max_len')  # 仅 string 类型需要

        if db_number is None or offset is None or value_type is None or value is None:
            raise ValueError("必须提供 db_number、offset、value_type 和 value")

        if value_type == 'int':
            data = bytearray(2)
            set_int(data, 0, int(value))
            self.client.db_write(db_number, offset, data)

        elif value_type == 'bool':
            if bit_index is None or not (0 <= bit_index <= 7):
                raise ValueError("bool 类型必须提供 bit_index (0~7)")
            data = self.client.db_read(db_number, offset, 1)  # 先读出原始字节
            set_bool(data, 0, bit_index, bool(value))
            self.client.db_write(db_number, offset, data)

        elif value_type == 'string':
            if string_max_len is None:
                raise ValueError("string 类型必须提供 string_max_len")
            data = bytearray(string_max_len + 2)
            set_string(data, 0, value, string_max_len)
            self.client.db_write(db_number, offset, data)

        else:
            raise ValueError(f"不支持的 value_type: {value_type}")