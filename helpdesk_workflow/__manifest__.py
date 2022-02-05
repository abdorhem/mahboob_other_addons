# -*- coding: utf-8 -*-
{
    'name': "Helpdek WorkFlow",

    'summary': """
       Add workflow in Helpdesk""",

    # 'description': """
    #     Long description of module's purpose
    # """,
    'author': "",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base','website_axis_helpdesk'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'security/groups.xml',
    ],
 
}
