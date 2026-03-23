from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NghiPhepNhanVien(models.Model):
    _name = "nghi_phep_nhan_vien"
    _description = "Nghỉ phép nhân viên"
    _rec_name = "ma_nghi_phep"
    _order = "ngay_bat_dau desc, id desc"

    ma_nghi_phep = fields.Char("Mã nghỉ phép", required=True, copy=False, default="New")
    nhan_vien_id = fields.Many2one("nhan_vien", string="Nhân viên", required=True)
    loai_nghi_phep = fields.Selection(
        [
            ("phep_nam", "Phép năm"),
            ("nghi_benh", "Nghỉ bệnh"),
            ("nghi_khong_luong", "Nghỉ không lương"),
            ("nghi_ca_nhan", "Nghỉ cá nhân"),
        ],
        string="Loại nghỉ phép",
        required=True,
        default="phep_nam",
    )
    ngay_bat_dau = fields.Date("Ngày bắt đầu", required=True)
    ngay_ket_thuc = fields.Date("Ngày kết thúc", required=True)
    so_ngay_nghi = fields.Float("Số ngày nghỉ", compute="_compute_so_ngay_nghi", store=True)
    ly_do = fields.Text("Lý do")
    trang_thai = fields.Selection(
        [
            ("nhap", "Nháp"),
            ("cho_duyet", "Chờ duyệt"),
            ("da_duyet", "Đã duyệt"),
            ("tu_choi", "Từ chối"),
        ],
        string="Trạng thái",
        default="nhap",
        required=True,
    )

    _sql_constraints = [
        ("ma_nghi_phep_unique", "unique(ma_nghi_phep)", "Mã nghỉ phép phải là duy nhất."),
    ]

    @api.depends("ngay_bat_dau", "ngay_ket_thuc")
    def _compute_so_ngay_nghi(self):
        for record in self:
            if record.ngay_bat_dau and record.ngay_ket_thuc:
                record.so_ngay_nghi = (record.ngay_ket_thuc - record.ngay_bat_dau).days + 1
            else:
                record.so_ngay_nghi = 0

    @api.constrains("ngay_bat_dau", "ngay_ket_thuc")
    def _check_ngay_nghi(self):
        for record in self:
            if record.ngay_bat_dau and record.ngay_ket_thuc and record.ngay_ket_thuc < record.ngay_bat_dau:
                raise ValidationError("Ngày kết thúc nghỉ phép không được nhỏ hơn ngày bắt đầu.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("ma_nghi_phep") or vals.get("ma_nghi_phep") == "New":
                vals["ma_nghi_phep"] = self.env["ir.sequence"].next_by_code(
                    "nhan_su.nghi_phep_nhan_vien"
                ) or "New"
        return super().create(vals_list)

    def action_gui_duyet(self):
        self.write({"trang_thai": "cho_duyet"})

    def action_duyet(self):
        self.write({"trang_thai": "da_duyet"})

    def action_tu_choi(self):
        self.write({"trang_thai": "tu_choi"})

    def action_dat_nhap(self):
        self.write({"trang_thai": "nhap"})
