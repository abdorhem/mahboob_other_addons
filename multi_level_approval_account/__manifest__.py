{
    'name': 'Odoo Approval: Accounting Extension',
    'version': '14.0.1.0',
    'category': 'Approvals',
    'live_test_url': 'https://demo14.domiup.com',
    'author': 'Domiup',
    'license': 'OPL-1',
    'support': 'domiup.contact@gmail.com',
    'website': 'https://apps.domiup.com/slides/odoo-approval-all-in-one-1',
    'depends': [
        'multi_level_approval',
        'account_accountant',
        'hr_expense',
        'purchase'
    ],
    'data': [
        'views/multi_approval_type_views.xml',
        'views/multi_approval_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'test': [],
    'demo': [],
    'installable': True,
    'active': False,
    'application': True,
}
