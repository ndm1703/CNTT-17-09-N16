from odoo import models, fields, api


class KhachHang(models.Model):
    _name = 'khach_hang'
    _description = 'Khách hàng'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    attachment_count = fields.Integer(
        string="Số hồ sơ",
        compute="_compute_attachment_count",
        store=True
    )

    ma_khach_hang = fields.Char(string="Mã khách hàng", required=True)
    name = fields.Char(string="Tên khách hàng", required=True)

    _sql_constraints = [
        ('ma_khach_hang_unique',
         'unique(ma_khach_hang)',
         'Mã khách hàng phải là duy nhất!')
    ]

    loai_khach = fields.Selection([
        ('ca_nhan', 'Cá nhân'),
        ('doanh_nghiep', 'Doanh nghiệp'),
    ], string="Loại khách", required=True)

    partner_id = fields.Many2one('res.partner', string='Liên kết partner')
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")
    dia_chi = fields.Text("Địa chỉ")
    thanh_pho = fields.Char("Thành phố")
    quoc_gia = fields.Char("Quốc gia")
    ma_so_thue = fields.Char("Mã số thuế")
    nguoi_dai_dien = fields.Char("Người đại diện")
    chuc_danh = fields.Char("Chức danh")
    so_tien_han_muc = fields.Float("Số tiền hạn mức")

    trang_thai = fields.Selection([
        ('tiem_nang', 'Tiềm năng'),
        ('hoat_dong', 'Hoạt động'),
        ('tam_dung', 'Tạm dừng'),
        ('ket_thuc', 'Kết thúc'),
    ], default='tiem_nang', string="Trạng thái")

    ghi_chu = fields.Text("Ghi chú")

    ngay_tao = fields.Datetime("Ngày tạo", default=fields.Datetime.now)
    ngay_cap_nhat = fields.Datetime("Ngày cập nhật", default=fields.Datetime.now)

    @api.depends("message_attachment_count")
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = record.message_attachment_count
    
