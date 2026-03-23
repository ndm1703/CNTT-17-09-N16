from odoo import models, fields, api
from datetime import date

from odoo.exceptions import ValidationError, UserError

class VanBanDi(models.Model):
    _name = 'van_ban_di'
    _description = 'Bảng chứa thông tin văn bản đi'
    _rec_name = 'ten_van_ban'

    so_van_ban_di = fields.Char("Số hiệu văn bản", required=True)
    ten_van_ban = fields.Char("Tên văn bản", required=True)
    so_hieu_van_ban = fields.Char("Số hiệu văn bản", required=True)
    noi_nhan = fields.Char("Nơi nhận")
    ngay_het_han = fields.Date(string='Ngày hết hạn')
    do_uu_tien = fields.Selection([
        ('thap', 'Thấp'),
        ('binh_thuong', 'Bình thường'),
        ('cao', 'Cao'),
        ('khan', 'Khẩn'),
    ], string='Độ ưu tiên', default='binh_thuong')
    trang_thai_xu_ly = fields.Selection([
        ('nhap', 'Nháp'),
        ('dang_xu_ly', 'Đang xử lý'),
        ('hoan_tat', 'Hoàn tất'),
    ], string='Trạng thái xử lý', default='nhap', required=True)
    file_data = fields.Binary(string='Tập tin')
    file_name = fields.Char(string='Tên tập tin')
    partner_id = fields.Many2one('res.partner', string="Đối tác", required=True)
    nhan_vien_xu_ly_id = fields.Many2one('hr.employee', string="Nhân viên xử lý", required=True)
    state = fields.Selection([
        ('con_han', 'Còn hạn'),
        ('sap_het_han', 'Sắp hết hạn'),
        ('het_han', 'Hết hạn'),
    ], string='Trạng thái', default='con_han', compute='_compute_state', store=True)
    so_ngay_con_lai = fields.Integer(string='Số ngày còn lại', compute='_compute_so_ngay_con_lai', store=True)
    ai_summary = fields.Text(string='Tóm tắt AI', readonly=True)
    ai_last_scan = fields.Datetime(string='Lần quét AI gần nhất', readonly=True)
    khach_hang_id = fields.Many2one('khach_hang', string='Khách hàng')
    ngay_xuat_ban = fields.Date(string='Ngày xuất bản')
    
    @api.depends('ngay_het_han')
    def _compute_state(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if not rec.ngay_het_han:
                rec.state = 'con_han'
                continue
            # compute days remaining
            try:
                remaining = (rec.ngay_het_han - fields.Date.from_string(today)).days
            except Exception:
                # fallback: use simple compare
                if rec.ngay_het_han < today:
                    rec.state = 'het_han'
                else:
                    rec.state = 'con_han'
                continue
            if remaining < 0:
                rec.state = 'het_han'
            elif remaining < 30:
                rec.state = 'sap_het_han'
            else:
                rec.state = 'con_han'

    @api.depends('ngay_het_han')
    def _compute_so_ngay_con_lai(self):
        today = fields.Date.context_today(self)
        today_date = fields.Date.from_string(today)
        for rec in self:
            if rec.ngay_het_han:
                rec.so_ngay_con_lai = (rec.ngay_het_han - today_date).days
            else:
                rec.so_ngay_con_lai = 0
    def _cron_update_states(self):
        # Cron job: recompute and write states so that stored field reflects current date
        records = self.search([])
        for rec in records:
            rec._compute_state()
            # write computed state back to record (no-op if unchanged)
            rec.write({'state': rec.state})
    @api.model
    def create(self, vals):
        # auto-generate document code if not provided using ir.sequence
        if not vals.get('so_van_ban_di'):
            seq_code = 'van_ban_di_code'
            seq = self.env['ir.sequence'].sudo().search([('code', '=', seq_code)], limit=1)
            if not seq:
                raise ValidationError('Sequence with code "%s" not found. Please create it in Settings > Technical > Sequences.' % seq_code)
            vals['so_van_ban_di'] = seq.next_by_id()
        return super(VanBanDi, self).create(vals)

    def action_quet_ai(self):
        self.ensure_one()
        if not self.file_data:
            raise UserError("Vui lòng tải lên một tập tin trước khi quét AI.")
        result = self.env['document.ai.service'].analyze_document(self.file_data, self.file_name)
        if not result:
            raise UserError("Không thể phân tích tài liệu.")
        vals = self._ai_values_from_result(result)
        if vals:
            vals['ai_last_scan'] = fields.Datetime.now()
            self.write(vals)
        return True

    def _ai_values_from_result(self, result):
        vals = {}
        if title := result.get('title'):
            vals['ten_van_ban'] = title
        if doc_number := result.get('document_number'):
            vals.setdefault('so_van_ban_di', doc_number)
            vals.setdefault('so_hieu_van_ban', doc_number)
        if recipient := result.get('recipient'):
            vals['noi_nhan'] = recipient
        if partner_text := result.get('partner'):
            partner = self.env['res.partner'].search([('name', 'ilike', partner_text)], limit=1)
            if partner:
                vals['partner_id'] = partner.id
        if date_str := result.get('due_date'):
            try:
                vals['ngay_het_han'] = fields.Date.from_string(date_str)
            except ValueError:
                pass
        if summary := result.get('summary'):
            vals['ai_summary'] = summary
        return vals

    @api.onchange('khach_hang_id')
    def _onchange_khach_hang(self):
        for rec in self:
            if rec.khach_hang_id and rec.khach_hang_id.partner_id:
                rec.partner_id = rec.khach_hang_id.partner_id

    def action_nhan_xu_ly(self):
        self.write({'trang_thai_xu_ly': 'dang_xu_ly'})

    def action_hoan_tat(self):
        self.write({'trang_thai_xu_ly': 'hoan_tat'})

    def action_dat_nhap(self):
        self.write({'trang_thai_xu_ly': 'nhap'})

    @api.constrains('ngay_xuat_ban', 'ngay_het_han')
    def _check_ngay_het_han(self):
        for rec in self:
            if rec.ngay_xuat_ban and rec.ngay_het_han and rec.ngay_het_han < rec.ngay_xuat_ban:
                raise ValidationError("Ngày hết hạn không được nhỏ hơn ngày xuất bản.")
