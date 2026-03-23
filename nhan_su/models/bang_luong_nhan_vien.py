from datetime import timedelta

from odoo import api, fields, models


class BangLuongNhanVien(models.Model):
    _name = "bang_luong_nhan_vien"
    _description = "Bảng lương nhân viên"
    _rec_name = "ma_bang_luong"
    _order = "nam desc, thang desc, id desc"

    ma_bang_luong = fields.Char("Mã bảng lương", required=True, copy=False, default="New")
    nhan_vien_id = fields.Many2one("nhan_vien", string="Nhân viên", required=True)
    hop_dong_id = fields.Many2one("hop_dong_nhan_vien", string="Hợp đồng")
    khen_thuong_xu_phat_ids = fields.One2many(
        "khen_thuong_xu_phat",
        "bang_luong_id",
        string="Quyết định thưởng/phạt",
    )
    thang = fields.Selection(
        [(str(month), "Tháng %s" % month) for month in range(1, 13)],
        string="Tháng",
        required=True,
        default=lambda self: str(fields.Date.context_today(self).month),
    )
    nam = fields.Integer("Năm", required=True, default=lambda self: fields.Date.context_today(self).year)
    luong_co_ban = fields.Float("Lương cơ bản")
    phu_cap = fields.Float("Phụ cấp")
    thuong = fields.Float("Thưởng")
    khau_tru = fields.Float("Khấu trừ")
    so_ngay_cong_chuan = fields.Float("Số ngày công chuẩn", default=26.0)
    he_so_tang_ca = fields.Float("Hệ số tăng ca", default=1.5)
    so_gio_tang_ca = fields.Float("Số giờ tăng ca", compute="_compute_tong_hop_nghi_phep", store=True)
    thuong_tang_ca = fields.Float("Thưởng tăng ca", compute="_compute_tong_hop_nghi_phep", store=True)
    he_so_phat_ve_som = fields.Float("Hệ số phạt về sớm", default=1.0)
    so_gio_ve_som = fields.Float("Số giờ về sớm", compute="_compute_tong_hop_nghi_phep", store=True)
    phat_ve_som = fields.Float("Phạt về sớm", compute="_compute_tong_hop_nghi_phep", store=True)
    so_ngay_phep_huong_luong = fields.Float("Nghỉ hưởng lương", compute="_compute_tong_hop_nghi_phep", store=True)
    so_ngay_nghi_khong_luong = fields.Float("Nghỉ không lương", compute="_compute_tong_hop_nghi_phep", store=True)
    so_ngay_nghi_khong_phep = fields.Float("Nghỉ không phép", compute="_compute_tong_hop_nghi_phep", store=True)
    khau_tru_nghi_phep = fields.Float("Khấu trừ nghỉ", compute="_compute_tong_hop_nghi_phep", store=True)
    tong_luong = fields.Float("Thực lĩnh", compute="_compute_tong_luong", store=True)
    trang_thai = fields.Selection(
        [
            ("nhap", "Nháp"),
            ("xac_nhan", "Đã xác nhận"),
            ("da_thanh_toan", "Đã thanh toán"),
        ],
        string="Trạng thái",
        default="nhap",
        required=True,
    )
    ghi_chu = fields.Text("Ghi chú")
    tong_thuong = fields.Float("Tổng thưởng", compute="_compute_tong_hop_thuong_phat", store=True)
    tong_phat = fields.Float("Tổng phạt", compute="_compute_tong_hop_thuong_phat", store=True)

    _sql_constraints = [
        ("ma_bang_luong_unique", "unique(ma_bang_luong)", "Mã bảng lương phải là duy nhất."),
    ]

    @api.depends(
        "luong_co_ban",
        "phu_cap",
        "thuong",
        "thuong_tang_ca",
        "khau_tru",
        "khau_tru_nghi_phep",
        "phat_ve_som",
    )
    def _compute_tong_luong(self):
        for record in self:
            record.tong_luong = (
                record.luong_co_ban
                + record.phu_cap
                + record.thuong
                + record.thuong_tang_ca
                - record.khau_tru
                - record.khau_tru_nghi_phep
                - record.phat_ve_som
            )

    @api.depends("khen_thuong_xu_phat_ids.so_tien", "khen_thuong_xu_phat_ids.loai")
    def _compute_tong_hop_thuong_phat(self):
        for record in self:
            rewards = record.khen_thuong_xu_phat_ids.filtered(lambda item: item.loai == "khen_thuong")
            penalties = record.khen_thuong_xu_phat_ids.filtered(lambda item: item.loai == "xu_phat")
            record.tong_thuong = sum(rewards.mapped("so_tien"))
            record.tong_phat = sum(penalties.mapped("so_tien"))

    @api.depends(
        "nhan_vien_id",
        "thang",
        "nam",
        "luong_co_ban",
        "so_ngay_cong_chuan",
        "he_so_tang_ca",
        "he_so_phat_ve_som",
    )
    def _compute_tong_hop_nghi_phep(self):
        leave_model = self.env["nghi_phep_nhan_vien"]
        attendance_model = self.env["cham_cong_nhan_vien"]
        for record in self:
            record.so_gio_tang_ca = 0
            record.thuong_tang_ca = 0
            record.so_gio_ve_som = 0
            record.phat_ve_som = 0
            record.so_ngay_phep_huong_luong = 0
            record.so_ngay_nghi_khong_luong = 0
            record.so_ngay_nghi_khong_phep = 0
            record.khau_tru_nghi_phep = 0
            if not record.nhan_vien_id or not record.thang or not record.nam:
                continue

            month = int(record.thang)
            start_date = fields.Date.to_date(f"{record.nam:04d}-{month:02d}-01")
            if month == 12:
                end_date = fields.Date.to_date(f"{record.nam + 1:04d}-01-01")
            else:
                end_date = fields.Date.to_date(f"{record.nam:04d}-{month + 1:02d}-01")
            month_last_day = end_date - timedelta(days=1)

            approved_leaves = leave_model.search(
                [
                    ("nhan_vien_id", "=", record.nhan_vien_id.id),
                    ("trang_thai", "=", "da_duyet"),
                    ("ngay_bat_dau", "<", fields.Date.to_string(end_date)),
                    ("ngay_ket_thuc", ">=", fields.Date.to_string(start_date)),
                ]
            )
            paid_leave_days = 0.0
            unpaid_leave_days = 0.0
            for leave in approved_leaves:
                overlap_start = max(leave.ngay_bat_dau, start_date)
                overlap_end = min(leave.ngay_ket_thuc, month_last_day)
                overlap_days = (overlap_end - overlap_start).days + 1 if overlap_end >= overlap_start else 0
                if leave.loai_nghi_phep in ("phep_nam", "nghi_benh"):
                    paid_leave_days += overlap_days
                elif leave.loai_nghi_phep == "nghi_khong_luong":
                    unpaid_leave_days += overlap_days

            unauthorized_leave_days = attendance_model.search_count(
                [
                    ("nhan_vien_id", "=", record.nhan_vien_id.id),
                    ("trang_thai", "=", "nghi_khong_phep"),
                    ("ngay_cham_cong", ">=", fields.Date.to_string(start_date)),
                    ("ngay_cham_cong", "<", fields.Date.to_string(end_date)),
                ]
            )
            overtime_records = attendance_model.search(
                [
                    ("nhan_vien_id", "=", record.nhan_vien_id.id),
                    ("ngay_cham_cong", ">=", fields.Date.to_string(start_date)),
                    ("ngay_cham_cong", "<", fields.Date.to_string(end_date)),
                ]
            )
            overtime_minutes = sum(overtime_records.mapped("so_phut_tang_ca"))
            early_leave_minutes = sum(overtime_records.mapped("so_phut_ve_som"))
            daily_salary = record.luong_co_ban / record.so_ngay_cong_chuan if record.so_ngay_cong_chuan else 0
            hourly_salary = daily_salary / 8 if daily_salary else 0
            record.so_ngay_phep_huong_luong = paid_leave_days
            record.so_ngay_nghi_khong_luong = unpaid_leave_days
            record.so_ngay_nghi_khong_phep = unauthorized_leave_days
            record.khau_tru_nghi_phep = (unpaid_leave_days + unauthorized_leave_days) * daily_salary
            record.so_gio_tang_ca = round(overtime_minutes / 60.0, 2)
            record.thuong_tang_ca = round(record.so_gio_tang_ca * hourly_salary * record.he_so_tang_ca, 2)
            record.so_gio_ve_som = round(early_leave_minutes / 60.0, 2)
            record.phat_ve_som = round(record.so_gio_ve_som * hourly_salary * record.he_so_phat_ve_som, 2)

    @api.onchange("hop_dong_id")
    def _onchange_hop_dong_id(self):
        for record in self:
            if not record.hop_dong_id:
                continue
            record.nhan_vien_id = record.hop_dong_id.nhan_vien_id
            record.luong_co_ban = record.hop_dong_id.luong_co_ban
            record.phu_cap = record.hop_dong_id.phu_cap
            record._sync_khen_thuong_xu_phat()

    @api.onchange("nhan_vien_id", "thang", "nam")
    def _onchange_ky_luong(self):
        for record in self:
            record._sync_khen_thuong_xu_phat()

    def _get_khen_thuong_xu_phat_domain(self):
        self.ensure_one()
        if not self.nhan_vien_id or not self.thang or not self.nam:
            return [("id", "=", False)]
        month = int(self.thang)
        start_date = fields.Date.to_date(f"{self.nam:04d}-{month:02d}-01")
        if month == 12:
            end_date = fields.Date.to_date(f"{self.nam + 1:04d}-01-01")
        else:
            end_date = fields.Date.to_date(f"{self.nam:04d}-{month + 1:02d}-01")
        return [
            ("nhan_vien_id", "=", self.nhan_vien_id.id),
            ("ngay", ">=", fields.Date.to_string(start_date)),
            ("ngay", "<", fields.Date.to_string(end_date)),
        ]

    def _sync_khen_thuong_xu_phat(self):
        for record in self:
            if not record.nhan_vien_id or not record.thang or not record.nam:
                record.khen_thuong_xu_phat_ids = [(5, 0, 0)]
                record.thuong = 0
                record.khau_tru = 0
                continue
            items = self.env["khen_thuong_xu_phat"].search(record._get_khen_thuong_xu_phat_domain())
            record.khen_thuong_xu_phat_ids = [(6, 0, items.ids)]
            record.thuong = sum(items.filtered(lambda item: item.loai == "khen_thuong").mapped("so_tien"))
            record.khau_tru = sum(items.filtered(lambda item: item.loai == "xu_phat").mapped("so_tien"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("ma_bang_luong") or vals.get("ma_bang_luong") == "New":
                vals["ma_bang_luong"] = self.env["ir.sequence"].next_by_code(
                    "nhan_su.bang_luong_nhan_vien"
                ) or "New"
        records = super().create(vals_list)
        records._sync_khen_thuong_xu_phat()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(field in vals for field in ("nhan_vien_id", "thang", "nam")):
            self._sync_khen_thuong_xu_phat()
        return res

    def action_xac_nhan(self):
        self.write({"trang_thai": "xac_nhan"})

    def action_thanh_toan(self):
        self.write({"trang_thai": "da_thanh_toan"})

    def action_dat_nhap(self):
        self.write({"trang_thai": "nhap"})

    def action_dong_bo_thuong_phat(self):
        self._sync_khen_thuong_xu_phat()
