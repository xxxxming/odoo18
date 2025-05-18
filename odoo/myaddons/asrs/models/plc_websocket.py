# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

class Plc_Websocket(models.Model):

    _inherit = 'plc.interface'


    @api.model
    def cron_fetch_plc_websocket(self):
        """
        定时任务
        """

        config = self.env['ir.config_parameter'].sudo()
        ip = config.get_param('192.168.0.10')
        port = int(config.get_param('202'))

        result = self.env['plc.controller'].read_plc_data(ip, port, register_address=0)
        logging.info(f"定时任务执行结果: {result}")

