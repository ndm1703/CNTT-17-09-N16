# -*- coding: utf-8 -*-
{
    'name': "Quản lý văn bản",

    'summary': """
        Quản lý văn bản đến, văn bản đi và loại văn bản
    """,

    'description': """
        Module hỗ trợ quản lý văn bản đến, văn bản đi, loại văn bản,
        tệp đính kèm và quy trình xử lý nội bộ.
    """,

    'author': "FIT-DNU",
    'website': "https://ttdn1501.aiotlabdnu.xyz/web",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Productivity',
    'version': '0.1',
    'application': True,
    'license': 'LGPL-3',
    'icon': '/quan_ly_van_ban/static/description/icon.png',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'web', 'nhan_su'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_van_ban.xml',
        'data/loai_van_ban_data.xml',
        'views/dashboard_van_ban.xml',
        'views/van_ban_den.xml',
        'views/van_ban_di.xml',
        'views/loai_van_ban.xml',
        'views/menu.xml',
        # inheritance for hr.employee form button
        'views/hr_employee_inherit.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'quan_ly_van_ban/static/src/scss/dashboard.scss',
            'quan_ly_van_ban/static/src/js/dashboard.js',
        ],
        'web.assets_qweb': [
            'quan_ly_van_ban/static/src/xml/dashboard.xml',
        ],
    },
}
