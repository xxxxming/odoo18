import logging
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from snap7.client import Client
import snap7
from odoo import models, api

_logger = logging.getLogger(__name__)

class PlcService(models.Model):
    _name = 'plc.service'
    _description = 'plc_service'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apscheduler.schedulers.background import BackgroundScheduler
        self.scheduler = BackgroundScheduler()
        self.plc_client = None
        self.scheduler.start()

    def start_plc_task(self):
        """启动 PLC 定时任务"""
        try:
            if not self.plc_client:
                self.plc_client = self._connect_plc()
            self._read_write_plc_data()
        except Exception as e:
            print(f"Error reading/writing PLC data: {e}")

    def _connect_plc(self):
        """连接到 PLC"""
        import snap7
        client = snap7.client.Client()
        client.connect('192.168.0.10', 0, 1)  # 替换为你的 PLC IP、机架号、槽号
        return client









    def _read_write_plc_data(self):
        """每 500ms 执行一次数据读写"""
        data = self.plc_client.db_read(1, 0, 4)  # 示例：读取 DB1 的 0-4 字节
        print(f"Read data: {data}")

        # 写入数据示例
        self.plc_client.db_write(1, 0, bytearray([0x01, 0x02, 0x03, 0x04]))

    def stop_plc_task(self):
        """停止调度器和 PLC 连接"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
        if self.plc_client and self.plc_client.get_connected():
            self.plc_client.disconnect()
            _logger.info("PLC 连接已关闭")


