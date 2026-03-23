from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrWorkHistory(models.Model):
    _name = 'hr.work.history'
    _description = 'Employee Work History'
    _order = 'date_start desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, ondelete='cascade')
    company_name = fields.Char(string='Company', required=True)
    position = fields.Char(string='Position')
    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date')

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_end and rec.date_start and rec.date_end < rec.date_start:
                raise ValidationError("Ngày kết thúc không được nhỏ hơn ngày bắt đầu!")
