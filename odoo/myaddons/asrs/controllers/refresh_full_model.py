from odoo import http
from odoo.http import request

class FullModelRefreshController(http.Controller):
    @http.route('/asrs/full_model_refresh', type='json', auth='user')
    def full_model_refresh(self, record_id):
        record = request.env['warehouse.system.operate'].browse(int(record_id))
        if not record.exists():
            return {}

        status_code = getattr(record, 'status_code', False)
        data = record.read()[0]
        data['status_code'] = status_code
        return data
