# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
import threading
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