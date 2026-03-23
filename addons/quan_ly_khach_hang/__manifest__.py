# -*- coding: utf-8 -*-
{
    "name": "quan_ly_khach_hang",
    "summary": "Quản lý khách hàng, cơ hội và chăm sóc khách hàng",
    "description": "Module QLKH với khách hàng, cơ hội, tương tác, hợp đồng, giao dịch, ghi chú, phản hồi, nhiệm vụ và marketing.",
    "author": "My Company",
    "website": "http://www.yourcompany.com",
    "category": "Sales/CRM",
    "version": "0.1",
    "depends": ["base", "mail"],
    "data": [
        "data/sequence_data.xml",
        "security/ir.model.access.csv",
        "views/qlkh_views.xml",
    ],
    "application": True,
}
