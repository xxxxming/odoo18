import snap7
import struct
from typing import List, Dict, Union


def auto_batch_read(
        plc_ip: str,
        data_layout: List[Dict],  # 预定义的数据结构
        rack: int = 0,
        slot: int = 1
) -> Dict[str, Union[str, int, float, bool, bytes]]:
    """
    自动批量读取PLC数据（基于预定义的结构）
    :param plc_ip: PLC IP地址
    :param data_layout: 数据结构定义，示例：
        [
            {
                'name': 'temperature',  # 数据名称
                'area': 'DB',           # 区域：DB/M/Q
                'db_number': 1,         # DB块号（仅area='DB'时需要）
                'address': 0,           # 起始地址（字节）
                'type': 'float',        # 类型：str/int/float/bool/byte
                'length': 4,            # 数据长度（float=4, int=2, str=总长度, bool=1）
                'bit_offset': None      # 位偏移（仅bool类型需要）
            },
            # ...更多数据项
        ]
    :return: 解析后的数据字典 {数据名称: 值}
    """
    client = snap7.client.Client()
    results = {}
    try:
        client.connect(plc_ip, rack, slot)
        if not client.get_connected():
            raise ConnectionError("PLC连接失败")

        for item in data_layout:
            name = item['name']
            area = item['area']
            addr = item['address']
            data_type = item['type']
            length = item['length']
            db_number = item.get('db_number', 0)
            bit_offset = item.get('bit_offset', 0)

            try:
                # 读取原始数据
                if area == 'DB':
                    raw_data = client.db_read(db_number, addr, length)
                elif area == 'M':
                    raw_data = client.mb_read(addr, length)
                elif area == 'Q':
                    raw_data = client.ab_read(addr, length)
                else:
                    raise ValueError(f"不支持的区域类型: {area}")

                # 解析数据
                if data_type == 'float':
                    value = struct.unpack('>f', raw_data)[0]
                elif data_type == 'int':
                    value = struct.unpack('>h', raw_data)[0]
                elif data_type == 'bool':
                    byte_val = raw_data[0]
                    value = bool(byte_val & (1 << bit_offset))
                elif data_type == 'str':
                    max_len = struct.unpack('>H', raw_data[0:2])[0]
                    actual_len = struct.unpack('>H', raw_data[2:4])[0]
                    value = raw_data[4:4 + actual_len].decode('utf-8').strip('\x00')
                elif data_type == 'byte':
                    value = bytes(raw_data)
                else:
                    value = None

                results[name] = value

            except Exception as e:
                results[name] = f"Error: {str(e)}"

    except Exception as e:
        results['global_error'] = f"全局错误: {str(e)}"
    finally:
        if client.get_connected():
            client.disconnect()

    return results


# 使用示例
if __name__ == "__main__":
    # 定义数据结构模板（提前配置）
    data_layout = [
        {
            'name': 'temperature',
            'area': 'DB',
            'db_number': 1,
            'address': 0,
            'type': 'float',
            'length': 4
        },
        {
            'name': 'status',
            'area': 'M',
            'address': 10,
            'type': 'bool',
            'length': 1,
            'bit_offset': 5  # M10.5
        },
        {
            'name': 'serial_number',
            'area': 'DB',
            'db_number': 1,
            'address': 14,
            'type': 'str',
            'length': 24  # 总长度=4字节头部+20字节内容
        }
    ]

    # 执行批量读取
    plc_data = auto_batch_read('192.168.0.1', data_layout)

    # 输出结果
    for key, value in plc_data.items():
        print(f"{key}: {value}")