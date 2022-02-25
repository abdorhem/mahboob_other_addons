
from dateutil.relativedelta import relativedelta
import calendar
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError


class HrPayrollOvertime(models.TransientModel):
    _name = "hr.payroll.overtime"
    _description = "HR Payroll Overtime"

    overtime_hours = fields.Float(default=0.0, string='Overtime Hours')

    def add_hours(self):
        record = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
        record.overtime_hours = self.overtime_hours
        return
