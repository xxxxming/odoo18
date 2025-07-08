# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
class FrameBarcode(models.Model):


    _name = 'frame.barcode'
    _description = 'inventory frame barcode'
    serial_number = fields.Integer(string='序号',readonly=True)
    frame_number = fields.Integer(string='框号')
    frame_barcode = fields.Char(string='框条码')
    # total_locations_id = fields.Many2one('warehouse.settings',string='框码定义',domain=[('total_locations','!=',0)])
    # total_locations = fields.Integer(related='total_locations_id.total_locations')

    # def increment_number(self):
    #     for record in self:
    #         record.serial_number += 1

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         # 如果vals中没有提供Serial_number或其为0，则自动生成
    #         if 'serial_number' not in vals or vals['serial_number'] == 0:
    #             # 查询当前序号最大的记录
    #             last_record = self.search([], order='serial_number desc', limit=1)
    #             if last_record:
    #                 new_serial = last_record.serial_number + 1
    #             else:
    #                 new_serial = 1
    #
    #             # 设置自动生成的字段值
    #             vals.update({
    #                 'serial_number': new_serial,
    #                 'frame_number': f"{new_serial:04d}",
    #                 'frame_barcode': f"PACK00000{new_serial:04d}"
    #             })
    #     return super().create(vals_list)


    def create_new_record(self):
        last_record = self.search([], order='serial_number desc', limit=1)
        if last_record:
            new_vals = {
                'serial_number': last_record.serial_number + 1,
                'frame_number': last_record.serial_number + 1,
                'frame_barcode': f"PACK000{last_record.serial_number + 1:04d}",
            }
        else:
            new_vals = {
                'serial_number': 1,
                'frame_number': '0001',
                'frame_barcode': 'PACK0000001',
            }
        return self.create(new_vals)

    def batch_create_records(self):
        # 获取目标数量，并确保其为整数
        settings = self.env['warehouse.settings'].search([], limit=1)
        location_count = settings.total_locations if isinstance(settings.total_locations, int) else 0

        if location_count <= 0:
            _logger.warning("无效的目标数量：%s", settings.total_locations)
            return

        # 获取最后一个记录的序列号
        last_record = self.search([], order='serial_number desc', limit=1)
        last_serial = last_record.serial_number if last_record else 0
        create_count = location_count - last_serial

        # 如果已有记录大于等于目标数量，则无需创建
        if last_serial >= location_count :
            _logger.info("已达到目标数量，无需继续创建")
            return

        # 创建新记录
        for i in range(create_count):
            if last_serial < location_count:
                self.create_new_record()
                last_serial += 1
            else:
                _logger.info("已达到目标数量，无需继续创建")

        _logger.info("总共需创建位置数量: %d", location_count)
