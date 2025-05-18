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

    @api.model
    def create(self, vals):
        if 'Serial_number' not in vals or vals['Serial_number'] == 0:
            last_record = self.search([], order='Serial_number desc', limit=1)
            if last_record:
                vals['Serial_number'] = last_record.Serial_number + 1
                vals['frame_number'] = f"{vals['Serial_number']:04d}"
                vals['frame_barcode'] = f"PACK00000{vals['Serial_number']:04d}"
            else:
                vals['Serial_number'] = 1
                vals['frame_number'] = '0001'
                vals['frame_barcode'] = 'PACK0000001'
        return super(FrameBarcode, self).create(vals)

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

