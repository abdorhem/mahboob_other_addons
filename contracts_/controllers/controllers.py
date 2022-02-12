# -*- coding: utf-8 -*-
# from odoo import http


# class Contract(http.Controller):
#     @http.route('/contract/contract/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/contract/contract/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('contract.listing', {
#             'root': '/contract/contract',
#             'objects': http.request.env['contract.contract'].search([]),
#         })

#     @http.route('/contract/contract/objects/<model("contract.contract"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('contract.object', {
#             'object': obj
#         })
