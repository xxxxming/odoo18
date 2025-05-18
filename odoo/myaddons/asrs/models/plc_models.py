
from odoo import models, fields, api
import snap7
import time
import struct
import logging




def connect_plc(ip='192.168.0.10', rack=0, slot=1, retries=3, retry_interval=5) -> snap7.client.Client:
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

def batch_read_plc(plc_ip: str, requests, rack: int = 0, slot: int = 1):
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
                        result['value'] = [struct.unpack('>h', raw_data[i * 2:(i + 1) * 2])[0] for i in range(count)]
                    elif data_type == 'float':
                        result['value'] = [struct.unpack('>f', raw_data[i * 4:(i + 1) * 4])[0] for i in range(count)]
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

def batch_to_plc(plc_ip: str,
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
                    f'>HH{str_length}s',  # 格式：最大长度(2字节) + 实际长度(2字节) + 内容
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
