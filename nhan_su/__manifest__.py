# -*- coding: utf-8 -*-
{
    'name': "nhan_su",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'license': 'LGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'mail', 'web', 'hr_recruitment'],

    # always loaded
    'data': [
        'data/sequence_data.xml',
        'security/ir.model.access.csv',
        'views/chuc_vu.xml',
        'views/don_vi.xml',
        'views/nhan_vien.xml',
        'views/dashboard_nhan_su.xml',
        'views/hop_dong_nhan_vien.xml',
        'views/bang_luong_nhan_vien.xml',
        'views/nghi_phep_nhan_vien.xml',
        'views/cham_cong_nhan_vien.xml',
        'views/khach_hang.xml',
        'views/lich_su_cong_tac.xml',
        'views/chung_chi_bang_cap.xml',
        'views/danh_sach_chung_chi_bang_cap.xml',
        'views/menu.xml',
        'views/hr_work_history.xml',
        'views/khen_thuong_xu_phat.xml',
        'views/hr_recruitment_ai_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'nhan_su/static/src/scss/dashboard.scss',
            'nhan_su/static/src/js/dashboard.js',
        ],
        'web.assets_qweb': [
            'nhan_su/static/src/xml/dashboard.xml',
        ],
    },
}
