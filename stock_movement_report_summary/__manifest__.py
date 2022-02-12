# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Inventory Movement Report Summary',
    'version': '14.0',
    'category': 'Warehouse',
    'summary': 'Inventory Movement Report (Onscreen, Excel and PDF)',
    'depends': ['stock_account', 'dwf', 'stock_movement_report'],
    'author': 'Synconics Technologies Pvt. Ltd.',
    'website': 'http://www.synconics.com',
    'description': """ Inventory movement report
    
    stock
    inventory
    movement
    report
    warehouse
    
""",
    'data': [
        'security/ir.model.access.csv',
        'wizard/stock_movement_wizard_view.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
