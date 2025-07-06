from odoo import http
from odoo.http import request

class RefreshStatusController(http.Controller):

    @http.route('/asrs/refresh_status', type='json', auth='user')
    def refresh_status(self, record_id):
        record = request.env['control.system.operate'].browse(int(record_id))
        if record.exists():
            return {
                'refresh_status': record.refresh_status,
                'storage_pack_number': record.storage_pack_number,
                'storage_base_number': record.storage_base_number,
                'storage_location_number': record.storage_location_number,
                'storage_pack_barcode': record.storage_pack_barcode,
            }
        return {}
