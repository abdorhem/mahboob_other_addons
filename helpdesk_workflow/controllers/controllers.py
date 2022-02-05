# -*- coding: utf-8 -*-
# from odoo import http


# class DesignRequest(http.Controller):
#     @http.route('/design_request/design_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/design_request/design_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('design_request.listing', {
#             'root': '/design_request/design_request',
#             'objects': http.request.env['design_request.design_request'].search([]),
#         })

#     @http.route('/design_request/design_request/objects/<model("design_request.design_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('design_request.object', {
#             'object': obj
#         })
