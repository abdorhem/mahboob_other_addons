# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Account Move Report Excel',
    'version': '14.0',
    'category': 'Accounting',
    'depends': ['account'],
    'author': 'Synconics Technologies Pvt. Ltd.',
    'website': 'http://www.synconics.com',
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_move_wizard_view.xml',
        'wizard/account_move_line_wizard_view.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
