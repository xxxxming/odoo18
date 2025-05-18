import snap7
import struct
import time
import struct
from snap7.util import get_int, get_real, get_bool, get_string
from typing import Union

def connect_plc(ip: str, rack=0, slot=1, retries=3, retry_interval=5) -> snap7.client.Client:
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
                print("连接成功!")
                return client
        except Exception as e:
            print(f"连接失败: {str(e)}")
            if attempt < retries:
                print(f"{retry_interval}秒后重试...")
                time.sleep(retry_interval)
    return None


def read_plc_data(client, area='DB', db_number=1, start_address=0,
                  data_type='int', bit_pos=0, str_len=20):
    """
    从PLC读取数据（支持多种数据类型）
    :param client: 已连接的client对象
    :param area: 区域类型 (DB/M/I/Q)
    :param db_number: DB块编号（仅当area=DB时有效）
    :param start_address: 起始地址（字节偏移）
    :param data_type: 数据类型（bit/byte/int/word/dint/real/string）
    :param bit_pos: 位位置（0-7）
    :param str_len: 字符串长度（字节）
    :return: 解析后的数据，失败返回None
    """
    if not client or not client.get_connected():
        print("错误：PLC未连接")
        return None

    try:
        # 确定区域代码和读取长度
        area_map = {
            'DB': (snap7.types.Areas.DB, db_number),
            'M': (snap7.types.Areas.MK, 0),
            'I': (snap7.types.Areas.PE, 0),
            'Q': (snap7.types.Areas.PA, 0)
        }
        if area not in area_map:
            raise ValueError("无效区域类型")

        area_code, db_num = area_map[area]
        read_size = {
            'bit': 1, 'byte': 1, 'int': 2, 'word': 2,
            'dint': 4, 'real': 4, 'string': str_len
        }[data_type]

        # 读取原始字节数据
        raw_data = client.read_area(area_code, db_num, start_address, read_size)

        # 数据解析
        if data_type == 'bit':
            return bool((raw_data[0] >> bit_pos) & 0x01)
        elif data_type == 'byte':
            return raw_data[0]
        elif data_type == 'int':
            return struct.unpack('>h', raw_data)[0]  # 16位有符号整数
        elif data_type == 'word':
            return struct.unpack('>H', raw_data)[0]  # 16位无符号整数
        elif data_type == 'dint':
            return struct.unpack('>i', raw_data)[0]  # 32位有符号整数
        elif data_type == 'real':
            return struct.unpack('>f', raw_data)[0]  # 32位浮点数
        elif data_type == 'string':
            return raw_data[2:2 + raw_data[1]].decode('utf-8').strip('\x00')  # 西门子字符串格式
        else:
            raise ValueError("不支持的数据类型")

    except Exception as e:
        print(f"数据读取失败: {str(e)}")
        return None

def write_to_plc(
        plc_ip: str,
        area: str,  # 区域: 'DB', 'M', 'Q'
        value: Union[bool, int, float, str, bytes, bytearray],
        db_number: int = 0,  # DB块号（必须明确指定！）
        address: int = 0,  # 字节地址
        bit_offset: int = -1,  # 位偏移（0-7，仅布尔类型需要）
        data_type: str = 'byte',  # 数据类型: bool/int/float/str/byte
        str_length: int = 20,  # 字符串总长度（仅字符串类型需要）
        rack: int = 0,  # 默认机架号
        slot: int = 1  # 默认插槽号
) -> bool:
    """
    通用PLC写入函数（强制使用 bytearray 类型）
    """
    client = snap7.client.Client()
    try:
        # --------------------------
        # 参数校验
        # --------------------------
        if area not in ['DB', 'M', 'Q']:
            raise ValueError("区域参数错误，只支持 'DB', 'M', 'Q'")

        if area == 'DB' and db_number == 0:
            raise ValueError("写入DB块时必须明确指定db_number参数！")

        if data_type == 'bool':
            if bit_offset == -1:
                raise ValueError("布尔类型必须指定 bit_offset (0-7)")
            if not (0 <= bit_offset <= 7):
                raise ValueError("bit_offset 必须在 0-7 范围内")
            if not isinstance(value, bool):
                raise TypeError("布尔类型的值必须是 True/False")

        # --------------------------
        # 连接PLC
        # --------------------------
        client.connect(plc_ip, rack, slot)
        if not client.get_connected():
            raise ConnectionError("PLC连接失败")

        # --------------------------
        # 数据转换（所有分支强制使用 bytearray）
        # --------------------------
        data_to_write = bytearray()


        # 布尔类型处理
        if data_type == 'bool':
            # 读取当前字节
            if area == 'DB':
                current_data = client.db_read(db_number, address, 1)
            elif area == 'M':
                current_data = client.mb_read(address, 1)
            elif area == 'Q':
                current_data = client.ab_read(address, 1)
            else:
                raise ValueError(f"不支持的布尔写入区域: {area}")

            current_byte = current_data[0]

            # 修改特定位
            if value:
                new_byte = current_byte | (1 << bit_offset)
            else:
                new_byte = current_byte & ~(1 << bit_offset)

            data_to_write = bytearray([new_byte])
            print(data_to_write)




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
                raise TypeError("字符串类型需要str值")
            encoded_str = value.encode('utf-8')
            print(encoded_str)
            # 关键点：计算实际需要存储的长度
            max_content_length = str_length - 2  # 减去头部2字节
            print(max_content_length)
            if len(encoded_str) > max_content_length:
                raise ValueError(f"字符串长度超出限制（最大{max_content_length}字节）")
            data_to_write = bytearray()
            #构造西门子字符串格式
            data_to_write += struct.pack(
                '>BB',
                max_content_length,  # 最大长度（2字节）
                len(encoded_str)
            )

            data_to_write += encoded_str.ljust(max_content_length, b'\x00')
            print(data_to_write)
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
        print(f"操作失败: {type(e).__name__}: {str(e)}")
        return False
    finally:
        if client.get_connected():
            client.disconnect()


def get_s7_string(data: bytearray, start: int) -> str:
    """
    兼容所有 snap7 版本，从 S7 字符串格式中提取字符串内容。
    参数:
        data: bytearray，从 db_read 返回
        start: 字符串起始偏移地址（STRING 类型的开头）
    返回:
        提取出的字符串（str）
    """
    max_len = data[start]
    real_len = data[start + 1]
    raw_bytes = data[start + 2 : start + 2 + real_len]
    return raw_bytes.decode('utf-8', errors='ignore')




# 示例用法
if __name__ == "__main__":
    #print(len('PACK00000001'))
    # 连接配置
    PLC_IP = "192.168.0.10"
    RACK = 0
    SLOT = 1

    # 建立连接
    plc_client = connect_plc(PLC_IP, RACK, SLOT)

    if plc_client:



        write_to_plc(
            plc_ip='192.168.0.10',
            area='DB',
            db_number=202,
            address=2,
            data_type='byte',
            value=123
        )

        # write_to_plc(
        #     plc_ip='192.168.0.10',
        #     area='DB',
        #     db_number=202,
        #     address=2,
        #     data_type='int',
        #     value=123
        # )

        # write_to_plc(
        #     plc_ip='192.168.0.10',
        #     area='DB',
        #     db_number=202,  # DB1
        #     address=0,  # DB1.DBX4.x
        #     bit_offset=1,  # 对应 DB1.DBX4.3
        #     data_type='bool',
        #     value=True
        # )

        # write_to_plc(
        #     plc_ip='192.168.0.10',
        #     area='DB',
        #     db_number=202,  # DB1
        #     address=14,  # 起始地址为0（DB2.DBB0）
        #     data_type='str',  # 数据类型为字符串
        #     value="PACK00000001",  # 要写入的字符串
        #     # value="Hello",  # 要写入的字符串
        #     #str_length=16
        # )

        # write_to_plc(
        #     plc_ip='192.168.0.10',
        #     area='DB',
        #     db_number=202,
        #     address=13,
        #     data_type='int',
        #     value=20
        # )

    else:
        print("无法建立PLC连接")














