# your_module/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
import logging

from .warehouse_communication import New_Public_PlcInterfaces

_logger = logging.getLogger(__name__)

class PlcScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.started = False

    def one_second_task(self):
        _logger.info("✅ 每秒执行一次 PLC 任务")
        # New_Public_PlcInterfaces().start_plc_scheduler()
        New_Public_PlcInterfaces().one_second_task()
    def start(self):
        if not self.started:
            _logger.info("🚀 启动 PLC 调度器")
            self.scheduler.add_job(self.one_second_task, 'interval', seconds=100, max_instances=1)
            self.scheduler.start()
            self.started = True
