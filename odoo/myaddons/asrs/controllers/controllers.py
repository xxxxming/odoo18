# -*- coding: utf-8 -*-
# from odoo import http


# class Asrs01(http.Controller):
#     @http.route('/asrs01/asrs01', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/asrs01/asrs01/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('asrs01.listing', {
#             'root': '/asrs01/asrs01',
#             'objects': http.request.env['asrs01.asrs01'].search([]),
#         })

#     @http.route('/asrs01/asrs01/objects/<model("asrs01.asrs01"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('asrs01.object', {
#             'object': obj
#         })

