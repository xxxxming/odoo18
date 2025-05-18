# -*- coding: utf-8 -*-
import struct
from odoo import models, fields, api
import logging
from snap7.util import *
from .plc_connect import PlcClient


class CommunicationProperty(models.Model):


    _name = 'communication.property'
    _description = 'communication property'
    name = fields.Char(string='名称')
    ip = fields.Char(string='IP地址')
    rack = fields.Integer(string='机架')
    slot = fields.Integer(string='插槽')



class PlcInterface(models.Model):


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


    @api.model
    def batch_read_plc(self, requests):
        """
        批量读取PLC数据（支持字符串、整数、浮点、布尔值）
        :param requests: 读取请求列表，每个请求格式为：
        :return: 结果列表，每个元素格式为：
            {
                'success': bool,
                'value': Union[str, int, float, bool, bytes],
                'error': str
            }
        """
        results = []
        try:
            for req in requests:
                result = {'success': False, 'value': None, 'error': ''}
                try:
                    address = req['address']
                    value_type = req['data_type']
                    db_number = req.get('db_number', 0)
                    # 根据数据类型计算读取参数
                    PlcClient.read(address, value_type,db_number)
                    result['success'] = True
                except Exception as e:
                    result['error'] = f"{type(e).__name__}: {str(e)}"
                results.append(result)
        except Exception as e:
            # 全局错误处理（如连接失败）
            results.append({'success': False, 'value': None, 'error': str(e)})
        return results

    @api.model
    def write_to_plc(self, db_number: 202, offset, value, value_type, bit_index=None, string_max_len=None):
        """
        写入数据到PLC，自动判断类型。
        参数：
        - client: snap7 client 实例
        - db_number: 数据块编号
        - offset: 起始偏移地址（字节）
        - value: 要写入的值
        - value_type: 类型字符串：'int'、'bool'、'string'
        - bit_index: 若为bool，指定字节内位索引（0~7）
        - string_max_len: 若为string，最大长度（如 STRING[20] => 20）
        """
        pass