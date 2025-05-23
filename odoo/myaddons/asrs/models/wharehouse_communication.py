# -*- coding: utf-8 -*-
import struct
from odoo import models, fields, api
import logging
import threading
from snap7.util import *
from .plc_connect import PlcClient
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
_logger = logging.getLogger(__name__)

plc_lock = threading.Lock()

class CommunicationProperty(models.Model):


    _name = 'communication.property'
    _description = 'communication property'
    name = fields.Char(string='名称')
    ip = fields.Char(string='IP地址')
    rack = fields.Integer(string='机架')
    slot = fields.Integer(string='插槽')






class Public_PlcInterface(models.Model):


    _name = 'plc.interface'
    _description = 'PLC Communication Interface'

    name = fields.Char(string='名称')
    ip = fields.Char(string='IP地址')
    rack = fields.Integer(string='机架')
    slot = fields.Integer(string='插槽')
    storage_goods_status = fields.Boolean(string='库位有货')
    cron_interval = fields.Integer(
        string='同步间隔(分钟)',
        default=5,
        help="数据同步频率（单位：分钟）"
    )
    cron_active = fields.Boolean(
        string='启用定时同步',
        default=True
    )
    # 急停状态
    emergency_stop_state = fields.Boolean(string='急停状态',default=False)




class New_Public_PlcInterfaces():


    def __init__(self):
        pass


    def batch_read_plc(self, data):
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
        # 根据数据类型计算读取参数
        code = PlcClient().set_db_number_read(data)
        return code

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

    def read_emergency_stop_state(self):
        # 临时测试
        return False
        # row = {'db_number': 202, 'start_address': 0, 'value_type': 'bool', 'bit_index': 0},
        # value = PlcClient().set_db_number_read(row)
        # _logger.info(f'{row_data.get("value_type")}查询结果：{value}')
        # return value

    def initialize_data_start(self):
        """
        hook调用
        """
        scheduler = self.start_plc_scheduler()
        _logger.info(scheduler)
        return scheduler


    def start_plc_scheduler(self):
        """启动定时任务"""
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            self.read_write_plc_data,
            'interval',
            seconds=0.2,
            max_instances=2
        )

        # 添加事件监听器
        def job_listener(event):
            if event.code == EVENT_JOB_EXECUTED:
                _logger.info(f"任务 {event.job_id} 返回结果: {event.retval}")
            elif event.code == EVENT_JOB_ERROR:
                _logger.error(f"任务失败: {event.exception}")
        scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        scheduler.start()
        return scheduler


    def read_write_plc_data(self):
        if plc_lock.locked():
            _logger.info("上一次任务未完成，本次跳过")
            return None
        with plc_lock:
            results = [
                {'db_number': 262, 'start_address': 0, 'value_type': 'bool', 'bit_index': 0},
                # 库位有货
            ]
            for result in results:
                row_results = self.batch_read_plc(result)
                return row_results
        _logger.info("读取完成")



    def do_something(self):
        _logger.info({
            'name': '访问触发',
            'type': 'server',
            'level': 'info',
            'message': f"用户 {user_id} 访问了页面 {page}",
            'path': __name__,
            'line': 'do_something',
            'func': 'do_something'
        })



























































