from odoo import http
from odoo.http import request

class FullModelRefreshController(http.Controller):
    @http.route('/asrs/full_model_refresh', type='json', auth='user')
    def full_model_refresh(self, record_id):
        record = request.env['control.system.operate'].browse(int(record_id))
        if not record.exists():
            return {}

        statut_code = getattr(record, 'statut_code', False)
        data = record.read()[0]
        data['statut_code'] = statut_code
        return data
