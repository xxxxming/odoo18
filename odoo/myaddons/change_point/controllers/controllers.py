# -*- coding: utf-8 -*-
# from odoo import http


# class ChangePoint(http.Controller):
#     @http.route('/change_point/change_point', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/change_point/change_point/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('change_point.listing', {
#             'root': '/change_point/change_point',
#             'objects': http.request.env['change_point.change_point'].search([]),
#         })

#     @http.route('/change_point/change_point/objects/<model("change_point.change_point"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('change_point.object', {
#             'object': obj
#         })

