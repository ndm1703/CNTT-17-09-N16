from odoo import models, fields, api
from odoo.exceptions import ValidationError

class KhenThuongXuPhat(models.Model):
    _name = 'khen_thuong_xu_phat'
    _description = 'Khen thưởng, xử phạt nhân sự'
    _rec_name = 'ten_su_kien'

    loai = fields.Selection([
        ('khen_thuong', 'Khen thưởng'),
        ('xu_phat', 'Xử phạt')
    ], string='Loại', required=True)
    ten_su_kien = fields.Char('Tên sự kiện', required=True)
    ngay = fields.Date('Ngày')
    so_quyet_dinh = fields.Char('Số quyết định')
    noi_dung = fields.Text('Nội dung')
    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên')
    nhan_su_id = fields.Many2one('hr.employee', string='Nhân sự')
    bang_luong_id = fields.Many2one('bang_luong_nhan_vien', string='Bảng lương')
    so_tien = fields.Monetary('Số tiền', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Đơn vị tiền tệ', default=lambda self: self.env.company.currency_id.id)
    ghi_chu = fields.Text('Ghi chú')

    @api.onchange('nhan_vien_id')
    def _onchange_nhan_vien_id(self):
        for record in self:
            if record.nhan_vien_id:
                record.nhan_su_id = False

    @api.constrains("nhan_vien_id", "nhan_su_id")
    def _check_target_employee(self):
        for record in self:
            if not record.nhan_vien_id and not record.nhan_su_id:
                raise ValidationError("Vui lòng chọn Nhân viên hoặc Nhân sự cho quyết định thưởng/phạt.")
