# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full
# copyright and licensing details.

{
    'name': 'Material Request',
    'version': '16.0',
    'summary': """This module allow your users to create Purchase Requests.""",
    'description': """
        This module allows users to create purchase request and links to
        request to stock picking.
    """,
    'author': 'Aktiv Software.',
    'website': 'http://www.aktivsoftware.com',
    'category': 'Warehouse',
    'depends': [
        'stock', 'internal_transfer_allow_user',
        'hr', 'dwf',
        'purchase', 'odoo_multi_branch', 'report_extended',
        'move_source_tracebility', 'stock_force_availability_app'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security_view.xml',
        'data/material_request_sequence.xml',
        'views/material_request_view.xml',
        'views/stock_picking_views.xml',
        'views/stock_scrap_views.xml',
        'views/group_scrap_orders.xml',
        'wizard/create_mo.xml',
        'report/material_request_report.xml',
        'report/report_register.xml',
    ],
    'installable': True,
    'application': False,
}
