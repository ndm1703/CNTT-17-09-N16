from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LichSuCongTac(models.Model):
    _name = "lich_su_cong_tac"
    _description = "Bảng chứa thông tin lịch sử công tác"

    nhan_vien_id = fields.Many2one("nhan_vien", string="Nhân viên")
    chuc_vu_id = fields.Many2one("chuc_vu", string="Chức vụ")
    don_vi_id = fields.Many2one("don_vi", string="Đơn vị")
    hr_department_id = fields.Many2one("hr.department", string="Phòng ban tuyển dụng")
    ngay_bat_dau = fields.Date("Ngày bắt đầu")
    ngay_ket_thuc = fields.Date("Ngày kết thúc")
    trang_thai = fields.Selection(
        [
            ("dang_cong_tac", "Đang công tác"),
            ("da_nghi", "Đã nghỉ"),
        ],
        compute="_compute_trang_thai",
        store=True,
    )
    loai_chuc_vu = fields.Selection(
        [
            ("Chính", "Chính"),
            ("Kiêm nhiệm", "Kiêm nhiệm"),
        ],
        string="Loại chức vụ",
        default="Chính",
    )

    @api.depends("ngay_bat_dau", "ngay_ket_thuc")
    def _compute_trang_thai(self):
        today = fields.Date.context_today(self)
        for record in self:
            if not record.ngay_ket_thuc or record.ngay_ket_thuc >= today:
                record.trang_thai = "dang_cong_tac"
            else:
                record.trang_thai = "da_nghi"

    @api.onchange("chuc_vu_id")
    def _onchange_chuc_vu_id(self):
        for record in self:
            if record.chuc_vu_id and record.chuc_vu_id.don_vi_id:
                record.don_vi_id = record.chuc_vu_id.don_vi_id
                record.hr_department_id = record.chuc_vu_id.don_vi_id.hr_department_id

    @api.onchange("don_vi_id")
    def _onchange_don_vi_id(self):
        for record in self:
            if record.don_vi_id:
                record.hr_department_id = record.don_vi_id.hr_department_id

    @api.onchange("hr_department_id")
    def _onchange_hr_department_id(self):
        for record in self:
            if record.hr_department_id and record.hr_department_id.don_vi_id:
                record.don_vi_id = record.hr_department_id.don_vi_id

    @api.model
    def create(self, vals):
        vals = self._sync_department_values(vals)
        if vals.get("nhan_vien_id") and not vals.get("ngay_ket_thuc"):
            old_jobs = self.search(
                [
                    ("nhan_vien_id", "=", vals["nhan_vien_id"]),
                    ("ngay_ket_thuc", "=", False),
                ]
            )
            old_jobs.write({"ngay_ket_thuc": fields.Date.today()})
        return super().create(vals)

    def write(self, vals):
        vals = self._sync_department_values(vals)
        return super().write(vals)

    @api.model
    def _sync_department_values(self, vals):
        synced_vals = dict(vals)
        if synced_vals.get("chuc_vu_id") and not synced_vals.get("don_vi_id"):
            chuc_vu = self.env["chuc_vu"].browse(synced_vals["chuc_vu_id"])
            if chuc_vu.don_vi_id:
                synced_vals["don_vi_id"] = chuc_vu.don_vi_id.id

        if synced_vals.get("don_vi_id") and not synced_vals.get("hr_department_id"):
            don_vi = self.env["don_vi"].browse(synced_vals["don_vi_id"])
            if don_vi.hr_department_id:
                synced_vals["hr_department_id"] = don_vi.hr_department_id.id
        elif synced_vals.get("hr_department_id") and not synced_vals.get("don_vi_id"):
            hr_department = self.env["hr.department"].browse(synced_vals["hr_department_id"])
            if hr_department.don_vi_id:
                synced_vals["don_vi_id"] = hr_department.don_vi_id.id
        return synced_vals

    @api.constrains("nhan_vien_id", "ngay_ket_thuc")
    def _check_unique_active_job(self):
        for record in self:
            if not record.ngay_ket_thuc:
                active_jobs = self.search(
                    [
                        ("nhan_vien_id", "=", record.nhan_vien_id.id),
                        ("id", "!=", record.id),
                        ("ngay_ket_thuc", "=", False),
                    ]
                )
                if active_jobs:
                    raise ValidationError(
                        "Nhân viên này đã có một công việc đang hoạt động. "
                        "Vui lòng kết thúc công việc cũ trước khi tạo công việc mới."
                    )
