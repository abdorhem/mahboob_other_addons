# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Outlet Sales Reports',
    'version': '13.0.2.0.0',
    'category': ' ',
    'summary': '',
    'sequence': '10',
    'author': '',
    'license': 'LGPL-3',
    'company': '',
    'maintainer': '',
    'support': '',
    'website': '',
    'depends': ["base", "web", 'odoo_multi_branch','stock_account','point_of_sale','stock','sale'],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizards/product_card_report.xml',
   
    ],
    "assets": {
        "web.assets_backend": [
            # "product_card_report/static/src/js/action_manager.js",
        ],
    },

    'images': ['static/description/banner.gif'],
}
