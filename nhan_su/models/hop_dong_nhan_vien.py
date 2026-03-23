from odoo import api, fields, models


class HopDongNhanVien(models.Model):
    _name = "hop_dong_nhan_vien"
    _description = "Hợp đồng nhân viên"
    _rec_name = "ma_hop_dong"
    _order = "ngay_bat_dau desc, id desc"

    ma_hop_dong = fields.Char("Mã hợp đồng", required=True, copy=False, default="New")
    nhan_vien_id = fields.Many2one("nhan_vien", string="Nhân viên", required=True)
    chuc_vu_id = fields.Many2one("chuc_vu", string="Chức vụ")
    loai_hop_dong = fields.Selection(
        [
            ("thu_viec", "Thử việc"),
            ("xac_dinh_thoi_han", "Xác định thời hạn"),
            ("khong_xac_dinh_thoi_han", "Không xác định thời hạn"),
            ("thoi_vu", "Thời vụ"),
        ],
        string="Loại hợp đồng",
        required=True,
        default="xac_dinh_thoi_han",
    )
    ngay_bat_dau = fields.Date("Ngày bắt đầu", required=True)
    ngay_ket_thuc = fields.Date("Ngày kết thúc")
    luong_co_ban = fields.Float("Lương cơ bản")
    phu_cap = fields.Float("Phụ cấp")
    ghi_chu = fields.Text("Ghi chú")
    trang_thai = fields.Selection(
        [
            ("hieu_luc", "Hiệu lực"),
            ("sap_het_han", "Sắp hết hạn"),
            ("het_han", "Hết hạn"),
        ],
        string="Trạng thái",
        compute="_compute_trang_thai",
        store=True,
    )

    _sql_constraints = [
        ("ma_hop_dong_unique", "unique(ma_hop_dong)", "Mã hợp đồng phải là duy nhất."),
    ]

    @api.depends("ngay_bat_dau", "ngay_ket_thuc")
    def _compute_trang_thai(self):
        today = fields.Date.context_today(self)
        for record in self:
            if not record.ngay_ket_thuc or record.ngay_ket_thuc >= today:
                if record.ngay_ket_thuc and (record.ngay_ket_thuc - today).days <= 30:
                    record.trang_thai = "sap_het_han"
                else:
                    record.trang_thai = "hieu_luc"
            else:
                record.trang_thai = "het_han"

    @api.onchange("chuc_vu_id")
    def _onchange_chuc_vu_id(self):
        for record in self:
            if record.chuc_vu_id and not record.luong_co_ban:
                record.luong_co_ban = record.chuc_vu_id.muc_luong_co_ban

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("ma_hop_dong") or vals.get("ma_hop_dong") == "New":
                vals["ma_hop_dong"] = self.env["ir.sequence"].next_by_code(
                    "nhan_su.hop_dong_nhan_vien"
                ) or "New"
        return super().create(vals_list)
