from odoo import models, fields, api
from datetime import date

from odoo.exceptions import ValidationError, UserError


class VanBanDen(models.Model):
    _name = 'van_ban_den'
    _description = 'Bảng chứa thông tin văn bản đến'
    _rec_name = 'ten_van_ban'
    partner_id = fields.Many2one('res.partner', string="Đối tác", required=True)
    nhan_vien_xu_ly_id = fields.Many2one('hr.employee', string="Nhân viên xử lý", required=True)    
    so_van_ban_den = fields.Char("Số văn bản đến", required=True)
    ten_van_ban = fields.Char("Tên văn bản", required=True)
    noi_gui_den = fields.Char("Nơi gửi đến")
    ngay_xuat_ban = fields.Date(string='Ngày xuất bản')
    khach_hang_id = fields.Many2one('khach_hang', string='Khách hàng')
    file_data = fields.Binary(string='Tập tin')
    file_name = fields.Char(string='Tên tập tin')
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
    state = fields.Selection([
        ('con_han', 'Còn hạn'),
        ('sap_het_han', 'Sắp hết hạn'),
        ('het_han', 'Hết hạn'),
    ], string='Trạng thái', default='con_han', compute='_compute_state', store=True)
    so_ngay_con_lai = fields.Integer(string='Số ngày còn lại', compute='_compute_so_ngay_con_lai', store=True)
    ai_summary = fields.Text(string='Tóm tắt AI', readonly=True)
    ai_last_scan = fields.Datetime(string='Lần quét AI gần nhất', readonly=True)

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
        if not vals.get('so_van_ban_den'):
            seq_code = 'quan_ly_van_ban.van_ban_den'
            try:
                vals['so_van_ban_den'] = self.env['ir.sequence'].next_by_code(seq_code) or '/'
            except Exception:
                # ignore sequence errors and let user provide code
                vals['so_van_ban_den'] = vals.get('so_van_ban_den') or '/'
        return super(VanBanDen, self).create(vals)

    @api.onchange('khach_hang_id')
    def _onchange_khach_hang(self):
        for rec in self:
            if rec.khach_hang_id and rec.khach_hang_id.partner_id:
                rec.partner_id = rec.khach_hang_id.partner_id

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
        if result.get('document_number') and not self.so_van_ban_den:
            vals['so_van_ban_den'] = result['document_number']
        if sender := result.get('sender'):
            vals['noi_gui_den'] = sender
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

    @api.model
    def get_dashboard_data(self):
        today = fields.Date.context_today(self)
        current_year = today.year
        van_ban_di_model = self.env['van_ban_di']
        all_incoming = self.search([])
        all_outgoing = van_ban_di_model.search([])
        all_documents = list(all_incoming) + list(all_outgoing)

        monthly_incoming = {month: 0 for month in range(1, 13)}
        monthly_outgoing = {month: 0 for month in range(1, 13)}
        for document in all_incoming.filtered('ngay_xuat_ban'):
            if document.ngay_xuat_ban.year == current_year:
                monthly_incoming[document.ngay_xuat_ban.month] += 1
        for document in all_outgoing.filtered('ngay_xuat_ban'):
            if document.ngay_xuat_ban.year == current_year:
                monthly_outgoing[document.ngay_xuat_ban.month] += 1

        employee_chart_map = {}
        for document in all_documents:
            employee_name = document.nhan_vien_xu_ly_id.name or 'Chưa phân công'
            employee_chart_map.setdefault(employee_name, 0)
            employee_chart_map[employee_name] += 1

        status_chart = [
            {'label': 'Nháp', 'value': len([rec for rec in all_documents if rec.trang_thai_xu_ly == 'nhap'])},
            {'label': 'Đang xử lý', 'value': len([rec for rec in all_documents if rec.trang_thai_xu_ly == 'dang_xu_ly'])},
            {'label': 'Hoàn tất', 'value': len([rec for rec in all_documents if rec.trang_thai_xu_ly == 'hoan_tat'])},
        ]
        priority_chart = [
            {'label': 'Thấp', 'value': len([rec for rec in all_documents if rec.do_uu_tien == 'thap'])},
            {'label': 'Bình thường', 'value': len([rec for rec in all_documents if rec.do_uu_tien == 'binh_thuong'])},
            {'label': 'Cao', 'value': len([rec for rec in all_documents if rec.do_uu_tien == 'cao'])},
            {'label': 'Khẩn', 'value': len([rec for rec in all_documents if rec.do_uu_tien == 'khan'])},
        ]

        return {
            'title': 'Tổng quan Văn bản',
            'current_year': current_year,
            'cards': [
                {
                    'label': 'Tổng văn bản',
                    'value': len(all_documents),
                    'theme': 'blue',
                    'action_xmlid': 'quan_ly_van_ban.action_van_ban_den',
                },
                {
                    'label': 'Văn bản đến',
                    'value': len(all_incoming),
                    'theme': 'green',
                    'action_xmlid': 'quan_ly_van_ban.action_van_ban_den',
                },
                {
                    'label': 'Văn bản đi',
                    'value': len(all_outgoing),
                    'theme': 'cyan',
                    'action_xmlid': 'quan_ly_van_ban.action_van_ban_di',
                },
                {
                    'label': 'Đang xử lý',
                    'value': len([rec for rec in all_documents if rec.trang_thai_xu_ly == 'dang_xu_ly']),
                    'theme': 'amber',
                    'action_xmlid': 'quan_ly_van_ban.action_van_ban_den',
                },
                {
                    'label': 'Hết hạn',
                    'value': len([rec for rec in all_documents if rec.state == 'het_han']),
                    'theme': 'red',
                    'action_xmlid': 'quan_ly_van_ban.action_van_ban_den',
                },
            ],
            'summary_sections': [
                {
                    'title': 'Tiến độ xử lý',
                    'theme': 'slate',
                    'items': [
                        {'label': 'Nháp', 'value': len([rec for rec in all_documents if rec.trang_thai_xu_ly == 'nhap'])},
                        {'label': 'Đang xử lý', 'value': len([rec for rec in all_documents if rec.trang_thai_xu_ly == 'dang_xu_ly'])},
                        {'label': 'Hoàn tất', 'value': len([rec for rec in all_documents if rec.trang_thai_xu_ly == 'hoan_tat'])},
                    ],
                },
                {
                    'title': 'Hạn xử lý',
                    'theme': 'cyan',
                    'items': [
                        {'label': 'Còn hạn', 'value': len([rec for rec in all_documents if rec.state == 'con_han'])},
                        {'label': 'Sắp hết hạn', 'value': len([rec for rec in all_documents if rec.state == 'sap_het_han'])},
                        {'label': 'Hết hạn', 'value': len([rec for rec in all_documents if rec.state == 'het_han'])},
                    ],
                },
            ],
            'shortcuts': [
                {'label': 'Văn bản đến', 'action_xmlid': 'quan_ly_van_ban.action_van_ban_den'},
                {'label': 'Văn bản đi', 'action_xmlid': 'quan_ly_van_ban.action_van_ban_di'},
                {'label': 'Loại văn bản', 'action_xmlid': 'quan_ly_van_ban.action_loai_van_ban'},
            ],
            'charts': {
                'monthly_incoming': [
                    {'label': f'Tháng {month}', 'value': monthly_incoming[month]}
                    for month in range(1, 13)
                ],
                'monthly_outgoing': [
                    {'label': f'Tháng {month}', 'value': monthly_outgoing[month]}
                    for month in range(1, 13)
                ],
                'employee_workload': [
                    {'label': name, 'value': value}
                    for name, value in sorted(employee_chart_map.items(), key=lambda item: (-item[1], item[0]))
                ],
                'status_distribution': status_chart,
                'priority_distribution': priority_chart,
            },
        }

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
