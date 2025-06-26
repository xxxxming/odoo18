from odoo import http
from odoo.http import request

class MyModelController(http.Controller):

    @http.route('/my_module/get_pack_number', type='json', auth='user')
    def get_pack_number(self, record_id):
        record = request.env['my.model'].sudo().browse(record_id)
        return {'pack_number': record.storage_pack_number}
