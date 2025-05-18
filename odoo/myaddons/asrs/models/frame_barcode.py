# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FrameBarcode(models.Model):


    _name = 'frame.barcode'
    _description = 'inventory frame barcode'
    Serial_number = fields.Integer(string='序号')
    frame_number = fields.Integer(string='框号')
    frame_barcode = fields.Char(string='框条码')

    def increment_number(self):
        for record in self:
            record.Serial_number += 1

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # 如果vals中没有提供Serial_number或其为0，则自动生成
            if 'Serial_number' not in vals or vals['Serial_number'] == 0:
                # 查询当前序号最大的记录
                last_record = self.search([], order='Serial_number desc', limit=1)
                if last_record:
                    new_serial = last_record.Serial_number + 1
                else:
                    new_serial = 1

                # 设置自动生成的字段值
                vals.update({
                    'Serial_number': new_serial,
                    'frame_number': f"{new_serial:04d}",
                    'frame_barcode': f"PACK00000{new_serial:04d}"
                })
        return super().create(vals_list)


    def create_new_record(self):
        last_record = self.search([], order='Serial_number desc', limit=1)
        if last_record:
            new_vals = {
                'Serial_number': last_record.Serial_number + 1,
                'frame_number': last_record.Serial_number + 1,
                'frame_barcode': f"PACK000{last_record.Serial_number + 1:04d}",
            }
        else:
            new_vals = {
                'Serial_number': 1,
                'frame_number': '0001',
                'frame_barcode': 'PACK0000001',
            }
        return self.create(new_vals)

