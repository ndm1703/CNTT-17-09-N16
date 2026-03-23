from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class DanhSachChungChiBangCap(models.Model):
    _name = 'danh_sach_chung_chi_bang_cap'
    _description = 'Bảng danh sách chứng chỉ bằng cấp'

    chung_chi_bang_cap_id = fields.Many2one("chung_chi_bang_cap", string="Chứng chỉ bằng cấp", required=True)
    level_id = fields.Many2one(
        "chung_chi_bang_cap_level",
        string="Cấp độ",
        domain="[('chung_chi_bang_cap_id', '=', chung_chi_bang_cap_id)]",
    )
    nhan_vien_id = fields.Many2one("nhan_vien", string="Nhân viên", required=True)
    ghi_chu = fields.Char("Ghi chú")
    ngay_cap = fields.Date("Ngày cấp")
    ngay_het_han = fields.Date("Ngày hết hạn")
    noi_cap = fields.Char("Nơi cấp")
    xep_loai = fields.Char("Xếp loại")
    trang_thai = fields.Selection(
        [
            ("con_han", "Còn hạn"),
            ("het_han", "Hết hạn"),
        ],
        string="Trạng thái",
        compute="_compute_trang_thai",
        store=True,
    )
    tep_dinh_kem = fields.Binary("Tệp đính kèm", attachment=True)
    ten_tep_dinh_kem = fields.Char("Tên tệp đính kèm")
    ma_dinh_danh = fields.Char("Mã định danh", related='nhan_vien_id.ma_dinh_danh')
    tuoi = fields.Integer("Tuổi", related='nhan_vien_id.tuoi')
    phan_loai = fields.Selection(
        related="chung_chi_bang_cap_id.phan_loai",
        string="Phân loại",
        store=True,
    )
    thoi_han_mac_dinh_thang = fields.Integer(
        related="chung_chi_bang_cap_id.thoi_han_mac_dinh_thang",
        string="Thời hạn mặc định (tháng)",
        store=True,
    )

    @api.depends("ngay_het_han")
    def _compute_trang_thai(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.ngay_het_han and record.ngay_het_han < today:
                record.trang_thai = "het_han"
            else:
                record.trang_thai = "con_han"

    @api.onchange("chung_chi_bang_cap_id", "ngay_cap")
    def _onchange_certificate_defaults(self):
        for record in self:
            if record.level_id and record.level_id.chung_chi_bang_cap_id != record.chung_chi_bang_cap_id:
                record.level_id = False
            expiry_date = record._get_default_expiry_date()
            if expiry_date:
                record.ngay_het_han = expiry_date

    def _get_default_expiry_date(self):
        self.ensure_one()
        months = self.chung_chi_bang_cap_id.thoi_han_mac_dinh_thang
        if not self.ngay_cap or not months or months <= 0:
            return False
        return self.ngay_cap + relativedelta(months=months)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("ngay_het_han"):
                continue
            issue_date = vals.get("ngay_cap")
            certificate_id = vals.get("chung_chi_bang_cap_id")
            if not issue_date or not certificate_id:
                continue
            certificate = self.env["chung_chi_bang_cap"].browse(certificate_id)
            months = certificate.thoi_han_mac_dinh_thang
            if months and months > 0:
                expiry_date = fields.Date.to_date(issue_date) + relativedelta(months=months)
                vals["ngay_het_han"] = fields.Date.to_string(expiry_date)
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if "ngay_het_han" in vals:
            return res
        if "ngay_cap" not in vals and "chung_chi_bang_cap_id" not in vals:
            return res
        for record in self:
            expiry_date = record._get_default_expiry_date()
            if expiry_date:
                record.ngay_het_han = expiry_date
        return res
