# -*- coding: utf-8 -*-
{
    'name': "User Requirement",
    'summary': """Create and Manage Company User Requirement""",
    'description': """Create and Manage Company User Requirement""",
    'author': "Witech Enterprise",
    'website': "http://witech.co.id",
    'category': 'Sales/Sales',
    'version': '0.1',
    'depends': ['sale','sale_management','portal'],
    'data': [
        # 'views/sequence.xml',
        'views/web_assets.xml',
        'views/sales_order.xml',
        'views/requirement_views.xml',
        'views/requirement_portal.xml',
        'report/user_requirement_template.xml',
        'report/report_menu.xml',
        'data/mail_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'auto_install': False
}
