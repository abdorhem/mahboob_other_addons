# -*- coding: utf-8 -*-
{
    'name': "Design Request",

    'summary': """
       Add Design & Offer Request Menues under Helpdesk""",

    # 'description': """
    #     Long description of module's purpose
    # """,
    'author': "",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base','website_axis_helpdesk'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
 
}
