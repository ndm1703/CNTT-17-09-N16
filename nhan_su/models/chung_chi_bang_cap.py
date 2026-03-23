from odoo import fields, models


class ChungChiBangCap(models.Model):
    _name = 'chung_chi_bang_cap'
    _description = 'Bảng chứa thông tin chứng chỉ bằng cấp'
    _rec_name = 'ten_chung_chi_bang_cap'

    ma_chung_chi_bang_cap = fields.Char("Mã chức chỉ, bằng cấp", required=True)
    ten_chung_chi_bang_cap = fields.Char("Tên chức chỉ, bằng cấp", required=True)
    phan_loai = fields.Selection(
        [
            ("bang_cap_chinh_quy", "Bằng cấp chính quy"),
            ("chung_chi_ngoai_ngu", "Chứng chỉ ngoại ngữ"),
            ("chung_chi_tin_hoc", "Chứng chỉ tin học"),
            ("chung_chi_ky_nang_mem", "Chứng chỉ kỹ năng mềm"),
        ],
        string="Phân loại",
        required=True,
        default="bang_cap_chinh_quy",
    )
    thoi_han_mac_dinh_thang = fields.Integer(
        "Thời hạn mặc định (tháng)",
        help="Nếu lớn hơn 0, hệ thống sẽ tự tính ngày hết hạn từ ngày cấp.",
    )
    level_ids = fields.One2many(
        "chung_chi_bang_cap_level",
        "chung_chi_bang_cap_id",
        string="Cấp độ",
    )


class ChungChiBangCapLevel(models.Model):
    _name = "chung_chi_bang_cap_level"
    _description = "Cấp độ chứng chỉ bằng cấp"
    _rec_name = "name"

    name = fields.Char("Cấp độ", required=True)
    code = fields.Char("Mã cấp độ")
    chung_chi_bang_cap_id = fields.Many2one(
        "chung_chi_bang_cap",
        string="Chứng chỉ bằng cấp",
        required=True,
        ondelete="cascade",
    )

    _sql_constraints = [
        (
            "uniq_level_per_certificate",
            "unique(chung_chi_bang_cap_id, name)",
            "Cấp độ đã tồn tại cho chứng chỉ/bằng cấp này.",
        ),
    ]
