from odoo import models, api, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    van_ban_count = fields.Integer(
        string="Số văn bản",
        compute="_compute_van_ban_count",
        help="Number of incoming documents this employee is handling",
    )

    def action_van_ban_phu_trach(self):
        self.ensure_one()
        return {
            'name': 'Văn bản phụ trách',
            'type': 'ir.actions.act_window',
            'res_model': 'van_ban_den',
            'view_mode': 'tree,form',
            'domain': [('nhan_vien_xu_ly_id', '=', self.id)],
            'context': {'default_nhan_vien_xu_ly_id': self.id},
        }

    def _compute_van_ban_count(self):
        for emp in self:
            emp.van_ban_count = self.env['van_ban_den'].search_count([
                ('nhan_vien_xu_ly_id', '=', emp.id)
            ])