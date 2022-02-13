# -*- coding: utf-8 -*-

{
    'name': 'Scrap Onscreen Report',
    'version': '14.0',
    'category': 'Stock',
    'author': 'Techultra Solutions',
    'website': '',
    'summary': 'Scrap Onscreen Report',
    'description': "Scrap Onscreen Report",
    'depends': ['dwf'],
    'data': [
        'views/assets_registry.xml',
        'views/scrap_report_views.xml',
        'views/res_config_settings_views.xml',
        'report/report_scrap_templates.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'auto_install': False,
    'installable': True,
}
