from odoo import api, models

class PlcServiceManager(models.Model):
    _name = 'plc.service.manager'
    _description = 'plc_service_manager'

    @api.model
    def start_plc_background_task(self):
        """供 ir.cron 调用的启动方法"""
        service = self.env['plc.service'].create({})
        service.start_plc_task()

