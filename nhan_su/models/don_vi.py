from odoo import api, fields, models


class DonVi(models.Model):
    _name = 'don_vi'
    _description = 'Bảng chứa thông tin đơn vị'
    _rec_name = 'ten_don_vi'

    ma_don_vi = fields.Char("Mã đơn vị", required=True)
    ten_don_vi = fields.Char("Tên đơn vị", required=True)
    truong_bo_phan_id = fields.Many2one(
        "nhan_vien",
        string="Trưởng bộ phận",
    )
    don_vi_cap_tren_id = fields.Many2one(
        "don_vi",
        string="Đơn vị cấp trên",
    )
    don_vi_con_ids = fields.One2many(
        "don_vi",
        "don_vi_cap_tren_id",
        string="Đơn vị cấp dưới",
    )
    hr_department_id = fields.Many2one(
        "hr.department",
        string="Phòng ban tuyển dụng",
    )
    chuc_vu_ids = fields.One2many(
        "chuc_vu",
        "don_vi_id",
        string="Chức vụ",
    )
    lich_su_cong_tac_ids = fields.One2many(
        "lich_su_cong_tac",
        "don_vi_id",
        string="Lịch sử công tác",
    )
    vi_tri_tuyen_dung_ids = fields.One2many(
        "hr.job",
        "don_vi_id",
        string="Vị trí tuyển dụng",
    )
    ung_vien_ids = fields.One2many(
        "hr.applicant",
        "don_vi_id",
        string="Ứng viên",
    )
    so_luong_nhan_vien = fields.Integer(
        string="Số lượng nhân viên",
        compute="_compute_so_luong_nhan_vien",
    )
    so_vi_tri_tuyen_dung = fields.Integer(
        string="Số vị trí tuyển dụng",
        compute="_compute_recruitment_totals",
    )
    so_ung_vien = fields.Integer(
        string="Số ứng viên",
        compute="_compute_recruitment_totals",
    )

    def _compute_so_luong_nhan_vien(self):
        lich_su_model = self.env["lich_su_cong_tac"]
        for record in self:
            record.so_luong_nhan_vien = lich_su_model.search_count(
                [
                    ("don_vi_id", "=", record.id),
                    ("ngay_ket_thuc", "=", False),
                ]
            )

    @api.depends("vi_tri_tuyen_dung_ids", "ung_vien_ids")
    def _compute_recruitment_totals(self):
        for record in self:
            record.so_vi_tri_tuyen_dung = len(record.vi_tri_tuyen_dung_ids)
            record.so_ung_vien = len(record.ung_vien_ids)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_hr_departments()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._sync_hr_departments()
        return res

    def _sync_hr_departments(self):
        for record in self.filtered("hr_department_id"):
            if record.hr_department_id.don_vi_id != record:
                record.hr_department_id.don_vi_id = record.id
