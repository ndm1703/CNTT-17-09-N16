from odoo import models, fields


class ChucVu(models.Model):
    _name = 'chuc_vu'
    _description = 'Bảng chứa thông tin chức vụ'
    _rec_name = 'ten_chuc_vu'

    ma_chuc_vu = fields.Char("Mã chức vụ", required=True)
    ten_chuc_vu = fields.Char("Tên chức vụ", required=True)
    don_vi_id = fields.Many2one("don_vi", string="Đơn vị")
    mo_ta_cong_viec = fields.Text("Mô tả công việc")
    muc_luong_co_ban = fields.Float("Mức lương cơ bản")
    cap_bac = fields.Char("Cấp bậc")
    yeu_cau_ky_nang_ids = fields.Many2many(
        "chung_chi_bang_cap",
        "chuc_vu_chung_chi_rel",
        "chuc_vu_id",
        "chung_chi_bang_cap_id",
        string="Yêu cầu kỹ năng",
    )
