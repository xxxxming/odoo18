# -*- coding: utf-8 -*-
import struct
from odoo import models, fields, api, http, Command, registry, SUPERUSER_ID
import logging
import threading
from odoo.http import request
from .control_system_operate import ControlSystemOperate
from .plc_connect import PlcClient
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
# from odoo.modules.registry import Registry
from .test import Tste_val

# from odoo.addons.bus.models.bus import Bus

import odoo
_logger = logging.getLogger(__name__)
scheduler_started = False
plc_lock = threading.Lock()

class CommunicationProperty(models.Model):

    _name = 'communication.property'
    _description = 'communication property'


    name = fields.Char(string='名称')
    ip = fields.Char(string='IP地址')
    rack = fields.Integer(string='机架')
    slot = fields.Integer(string='插槽')


class SystemControl(models.Model):

    _name = 'system.control'
    _description = 'system control'


    emergency_stop = fields.Boolean(string="紧急停止", default=True)
    manual_control = fields.Boolean(string="手动控制")
    auto_control = fields.Boolean(string="自动控制")
    start = fields.Boolean(string="开始")
    stop = fields.Boolean(string="停止")
    pause = fields.Boolean(string="暂停")
    reset = fields.Boolean(string="复位")
    one_second = fields.Integer(string='一秒周期',store=True)


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
    emergency_stop_state = fields.Boolean(string='急停状态',default=False,)


class New_Public_PlcInterfaces:

    _name = 'new.public.interface'
    _description = 'new public interface'
    def __init__(self, env):
        self.env = env
        self.one_second = 0

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

    #@api .model
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
        # scheduler.add_job(
        #     self.read_write_plc_data,
        #     'interval',
        #     seconds=0.5,
        #     max_instances=2
        # )
        # 1秒的定时任务
        _logger.info("1秒的定时任务")
        scheduler.add_job(
            self.one_second_task,  # 可以指向另一个方法
            'interval',
            seconds=10,
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
        results = [
            # PC控制
            {'db_number': 260, 'offset': 0, 'value_type': 'bool', 'bit_index': 0},
            {'db_number': 260, 'offset': 0, 'value_type': 'bool', 'bit_index': 1},
            {'db_number': 260, 'offset': 0, 'value_type': 'bool', 'bit_index': 2},
            {'db_number': 260, 'offset': 0, 'value_type': 'bool', 'bit_index': 3},
            {'db_number': 260, 'offset': 0, 'value_type': 'bool', 'bit_index': 4},
            {'db_number': 260, 'offset': 0, 'value_type': 'bool', 'bit_index': 5},
            {'db_number': 260, 'offset': 0, 'value_type': 'bool', 'bit_index': 6},
            {'db_number': 260, 'offset': 0, 'value_type': 'bool', 'bit_index': 7},
        ]
        num = 0
        for result in results:
            num += 1
            value = self.batch_read_plc(result)
            if num == 1:
                SystemControl.start = value
                print(SystemControl.start)
                # record = self.env['system.control'].search([], limit=1)
                # try:
                #     record.write({'start': value})
            elif num == 2:
                SystemControl.stop = value
            elif num == 3:
                SystemControl.pause = value
            elif num == 4:
                SystemControl.reset = value


    def one_second_task(self):
        """1S执行"""

        _logger.info("1秒的定时任务")
        return None
        # 获取所有 ControlSystemOperate 记录
        # control_records = self.env['control.system.operate'].search([])
        # for record in control_records:
        #     record.one_second = self.one_second
        # print(record.one_second)

    def ten_second_task(self):
        """1S执行"""
        # information real

        #修改后：
        # from odoo.modules.registry import Registry
        # registry = Registry('odoo18e')
        # 修改后：
        # with registry.cursor() as cr:
        #     env = api.Environment(cr, SUPERUSER_ID, {})
        #
        # record = env['control.system.operate'].search([], limit=1)
        # if record:
        #     record.storage_information_read()  # 执行数据更新
        #     record.modified([
        #         'storage_goods_status',
        #         'storage_pack_number',
        #         'storage_location_number',
        #         'storage_pack_barcode'
        #     ])
        #     self.env.flush_all()  # 强制刷新 ORM 缓存

        # 手动获取游标
        # db_name = 'odoo18e'  # ← 修改为你自己的数据库名
        #
        # with odoo.sql_db.db_connect(db_name).cursor() as cr:
        #     env = api.Environment(cr, 1, {})  # 1 表示超级管理员 user_id
        # try:
            # 调用 New_Public_PlcInterfaces 类的 one_second_task 方法
            # New_Public_PlcInterfaces().read_write_plc_data()
            # ControlSystemOperate().fetch_plc()
            #

        #         self.env['control.system.operate'].storage_information_read()
        #         self.env['control.system.operate'].modified([
        #             'storage_goods_status',
        #             'storage_pack_number',
        #             'storage_location_number',
        #             'storage_pack_barcode'
        #         ])
        #         self.env.flush_all()  # 强制刷新 ORM 缓存)
        #
        # except Exception as e:
        #     # 记录异常信息
        #     _logger.error(f"PLC 每10秒任务发生错误: {str(e)}")

        with (self.env.registry.cursor() as new_cr):
             new_env = api.Environment(new_cr, self.env.uid, {})
             new_env['control.system.operate'].storage_information_read()
            # new_env['control.system.operate'].stacker_information_read()
            # new_env['control.system.operate'].entrance1_information_read()
            # new_env['control.system.operate'].entrance2_information_read()


        # self.env['control.system.operate'].storage_information_read()

        # if not self.env.cr.closed:
        #     _logger.info("Cursor 1 is open.")
        # else:
        #     _logger.info("Cursor 1 is closed.")

        # self.env['control.system.operate'].storage_information_read()
        # self.env['control.system.operate'].stacker_information_read()
        # self.env['control.system.operate'].entrance1_information_read()
        # self.env['control.system.operate'].entrance2_information_read()

        # self.env.cr.execute("SELECT * FROM control_system_operate")  # 显式检查游标有效性
        # if self.env.cr.closed:
        #     self.env.cr = self.env.registry.cursor()  # 重建游标
        #
        # try:
        #   # self.storage_information_read()
        #   self.env['control.system.operate'].storage_information_read()
        # finally:
        #     if not self.env.cr.closed:  # 避免重复关闭
        #         self.env.cr.close()

        # partner = self.env['control.system.operate'].create({'name': 'MyPartner1'})
        # args = [[1]],
        # kwargs = {"context": {
        #     "lang": "zh_CN",
        #     "tz": "Asia/Shanghai",
        #     "uid": 2,
        #     "allowed_company_ids": [1]}
        # },
        # api.call_kw(new_env['control.system.operate'],'storage_information_read', args,kwargs)

        # if not self.env.cr.closed:
        #     _logger.info("Cursor 2 is open.")
        # else:
        #     _logger.info("Cursor 2 is closed.")

        # self.read_write_plc_data()
        # _logger.info("information 10 second")
        return None
        # """1S执行"""
        # try:
        #
        #     _logger.info("10秒的定时任务")
        # except Exception as e:
        #     _logger.error("[ten_second_task] 执行过程中发生异常: %s", str(e), exc_info=True)
        # return None


    # def do_something(self):
    #     _logger.info({
    #         'name': '访问触发',
    #         'type': 'server',
    #         'level': 'info',
    #         'message': f"用户 {user_id} 访问了页面 {page}",
    #         'path': __name__,
    #         'line': 'do_something',
    #         'func': 'do_something'
    #     })

    # def safe_call_entrance2_information_read(self):
    #     try:
    #         _logger.info("开始调用 entrance2_information_read 方法")
    #         result = self.env['control.system.operate'].call_kw('storage_information_read', [], {})
    #         _logger.info("调用成功，返回结果: %s", result)
    #         return result
    #     except Exception as e:
    #         _logger.error("调用 entrance2_information_read 方法失败: %s", str(e))
    #         raise

















































