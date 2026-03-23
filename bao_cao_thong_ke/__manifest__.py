# -*- coding: utf-8 -*-
{
    "name": "Báo cáo thống kê",
    "version": "0.1",
    "summary": "Tổng hợp số liệu tuyển dụng từ mô-đun Ứng viên",
    "description": "Báo cáo số ứng viên, CV và các buổi phỏng vấn theo vị trí và tháng.",
    "author": "My Company",
    "license": "LGPL-3",
    "depends": ["base", "ung_vien"],
    "data": [
        "security/ir.model.access.csv",
        "views/bao_cao_thong_ke_views.xml",
    ],
    "installable": True,
    "application": False,
}
