from dateutil.relativedelta import relativedelta
import calendar
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError


class HrPayslip(models.Model):
    _name = "employee.late.history"
    _description = "Employee Late History"

    employee_id = fields.Many2one('hr.employee',string='Employee')
    badge_id = fields.Char("Employee Badge Id")
    date_start = fields.Date('Date Start')
    date_end = fields.Date('Date End')
    late_hour = fields.Float("Late Hours")
    overtime_hour = fields.Float("Overtime Hours")


class HrEmployee(models.Model):
    _inherit='hr.employee'

    def show_emp_late_history(self):
        for rec in self:
            late_action = self.env.ref('saudi_hr_payroll.action_employee_late_history')
            late_action = late_action.read()[0]
            late_action['domain'] = str([('employee_id', '=', rec.id)])
        return late_action
