from apscheduler.schedulers.background import BackgroundScheduler
import logging
from .warehouse_communication import New_Public_PlcInterfaces

_logger = logging.getLogger(__name__)

class PlcScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.started = False

    def one_second_task(self):
        """
        每秒执行的任务，调用 New_Public_PlcInterfaces 的 one_second_task 方法。
        用于处理与 PLC（可编程逻辑控制器）的通信任务。
        """
        try:
            # 调用 New_Public_PlcInterfaces 类的 one_second_task 方法
            New_Public_PlcInterfaces().one_second_task()
        except Exception as e:
            # 记录异常信息
            _logger.error(f"PLC 每秒任务发生错误: {str(e)}")

    def start(self):
        """
        启动调度器，初始化定时任务。
        如果调度器未启动，则添加每100秒执行一次的one_second_task任务，
        并启动调度器。
        """
        if not self.started:
            _logger.info("🚀 启动 PLC 调度器")
            # 添加间隔任务：每100秒调用一次 one_second_task 方法
            self.scheduler.add_job(self.one_second_task, 'interval', seconds=100, max_instances=1)
            # 启动后台调度器
            self.scheduler.start()
            self.started = True
