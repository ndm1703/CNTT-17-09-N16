from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ChamCongNhanVien(models.Model):
    _name = "cham_cong_nhan_vien"
    _description = "Chấm công nhân viên"
    _rec_name = "ma_cham_cong"
    _order = "ngay_cham_cong desc, id desc"

    ma_cham_cong = fields.Char("Mã chấm công", required=True, copy=False, default="New")
    nhan_vien_id = fields.Many2one("nhan_vien", string="Nhân viên", required=True)
    ngay_cham_cong = fields.Date("Ngày chấm công", required=True, default=fields.Date.context_today)
    gio_vao_chuan = fields.Float("Giờ vào chuẩn", default=8.0)
    gio_ra_chuan = fields.Float("Giờ ra chuẩn", default=17.0)
    gio_vao = fields.Float("Giờ vào")
    gio_ra = fields.Float("Giờ ra")
    so_gio_lam_viec = fields.Float("Số giờ làm việc", compute="_compute_so_gio_lam_viec", store=True)
    so_phut_di_muon = fields.Integer("Phút đi muộn", compute="_compute_time_metrics", store=True)
    so_phut_ve_som = fields.Integer("Phút về sớm", compute="_compute_time_metrics", store=True)
    so_phut_tang_ca = fields.Integer("Phút tăng ca", compute="_compute_time_metrics", store=True)
    trang_thai = fields.Selection(
        [
            ("co_mat", "Có mặt"),
            ("di_muon", "Đi muộn"),
            ("ve_som", "Về sớm"),
            ("nghi_phep", "Nghỉ phép"),
            ("nghi_khong_phep", "Nghỉ không phép"),
            ("cong_tac", "Công tác"),
        ],
        string="Trạng thái",
        required=True,
        default="co_mat",
    )
    ghi_chu = fields.Text("Ghi chú")

    _sql_constraints = [
        ("ma_cham_cong_unique", "unique(ma_cham_cong)", "Mã chấm công phải là duy nhất."),
        ("nhan_vien_ngay_unique", "unique(nhan_vien_id, ngay_cham_cong)", "Mỗi nhân viên chỉ có một bản ghi chấm công trong ngày."),
    ]

    @api.depends("gio_vao", "gio_ra")
    def _compute_so_gio_lam_viec(self):
        for record in self:
            if record.gio_vao is not False and record.gio_ra is not False and record.gio_ra >= record.gio_vao:
                record.so_gio_lam_viec = record.gio_ra - record.gio_vao
            else:
                record.so_gio_lam_viec = 0

    @api.depends("gio_vao", "gio_ra", "gio_vao_chuan", "gio_ra_chuan")
    def _compute_time_metrics(self):
        for record in self:
            late_minutes = 0
            early_minutes = 0
            overtime_minutes = 0
            if record.gio_vao is not False and record.gio_vao_chuan is not False and record.gio_vao > record.gio_vao_chuan:
                late_minutes = int(round((record.gio_vao - record.gio_vao_chuan) * 60))
            if record.gio_ra is not False and record.gio_ra_chuan is not False and record.gio_ra < record.gio_ra_chuan:
                early_minutes = int(round((record.gio_ra_chuan - record.gio_ra) * 60))
            if record.gio_ra is not False and record.gio_ra_chuan is not False and record.gio_ra > record.gio_ra_chuan:
                overtime_minutes = int(round((record.gio_ra - record.gio_ra_chuan) * 60))
            record.so_phut_di_muon = late_minutes
            record.so_phut_ve_som = early_minutes
            record.so_phut_tang_ca = overtime_minutes

    @api.constrains("gio_vao", "gio_ra", "gio_vao_chuan", "gio_ra_chuan")
    def _check_gio_lam_viec(self):
        for record in self:
            if record.gio_vao is not False and (record.gio_vao < 0 or record.gio_vao > 24):
                raise ValidationError("Giờ vào phải nằm trong khoảng từ 0 đến 24.")
            if record.gio_ra is not False and (record.gio_ra < 0 or record.gio_ra > 24):
                raise ValidationError("Giờ ra phải nằm trong khoảng từ 0 đến 24.")
            if record.gio_vao_chuan is not False and (record.gio_vao_chuan < 0 or record.gio_vao_chuan > 24):
                raise ValidationError("Giờ vào chuẩn phải nằm trong khoảng từ 0 đến 24.")
            if record.gio_ra_chuan is not False and (record.gio_ra_chuan < 0 or record.gio_ra_chuan > 24):
                raise ValidationError("Giờ ra chuẩn phải nằm trong khoảng từ 0 đến 24.")
            if (
                record.gio_vao is not False and record.gio_ra is not False
                and record.gio_ra < record.gio_vao
            ):
                raise ValidationError("Giờ ra không được nhỏ hơn giờ vào.")
            if (
                record.gio_vao_chuan is not False and record.gio_ra_chuan is not False
                and record.gio_ra_chuan < record.gio_vao_chuan
            ):
                raise ValidationError("Giờ ra chuẩn không được nhỏ hơn giờ vào chuẩn.")

    def _sync_time_status(self):
        for record in self:
            if record.trang_thai in ("nghi_phep", "nghi_khong_phep", "cong_tac"):
                continue
            if record.so_phut_di_muon > 0:
                record.trang_thai = "di_muon"
            elif record.so_phut_ve_som > 0:
                record.trang_thai = "ve_som"
            else:
                record.trang_thai = "co_mat"

    def _sync_leave_status(self):
        leave_model = self.env["nghi_phep_nhan_vien"]
        for record in self:
            if not record.nhan_vien_id or not record.ngay_cham_cong:
                continue
            approved_leave = leave_model.search(
                [
                    ("nhan_vien_id", "=", record.nhan_vien_id.id),
                    ("trang_thai", "=", "da_duyet"),
                    ("ngay_bat_dau", "<=", record.ngay_cham_cong),
                    ("ngay_ket_thuc", ">=", record.ngay_cham_cong),
                ],
                limit=1,
            )
            if approved_leave:
                record.trang_thai = "nghi_phep"
            elif record.trang_thai == "nghi_phep":
                record._sync_time_status()

    @api.onchange("nhan_vien_id", "ngay_cham_cong")
    def _onchange_leave_status(self):
        self._sync_leave_status()

    @api.onchange("gio_vao", "gio_ra", "gio_vao_chuan", "gio_ra_chuan")
    def _onchange_time_status(self):
        self._sync_time_status()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("ma_cham_cong") or vals.get("ma_cham_cong") == "New":
                vals["ma_cham_cong"] = self.env["ir.sequence"].next_by_code(
                    "nhan_su.cham_cong_nhan_vien"
                ) or "New"
        records = super().create(vals_list)
        records._sync_leave_status()
        records._sync_time_status()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(field in vals for field in ("nhan_vien_id", "ngay_cham_cong")):
            self._sync_leave_status()
        if any(field in vals for field in ("gio_vao", "gio_ra", "gio_vao_chuan", "gio_ra_chuan")):
            self._sync_time_status()
        return res
