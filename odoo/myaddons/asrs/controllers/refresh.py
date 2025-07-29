from odoo import http
from odoo.http import request

class RefreshStatusController(http.Controller):

    @http.route('/asrs/refresh_status', type='json', auth='user', log=False)
    def refresh_status(self, record_id):
        record = request.env['warehouse.system.operate'].browse(int(record_id))
        if record.exists():
            # 增加刷新字段
            return {

                'refresh_status': record.refresh_status,
                'allow_move_stock': record.allow_move_stock,
                'allow_store': record.allow_store,
                'allow_outbound': record.allow_outbound,
                'allow_return': record.allow_return,
                'pack_barcode': record.pack_barcode,
                'location_number': record.location_number,
                'source_target': record.source_target,
                'new_target': record.new_target,

            }
        return {}
