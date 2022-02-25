# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError


class HrPayslip(models.Model):
    _name = "hr.payslip"
    _inherit = ['hr.payslip','mail.thread']


    branch_outlet_id = fields.Many2one(
        'res.branch.outlet',
        string="Outlet",
        compute='_compute_branch_outlet_id',
        copy=False,
        default=lambda self: self.env.user.branch_outlet_id.id, tracking=True
    )
    company_branch_id = fields.Many2one(
        'res.company.branch', string="Company Branch",
        related='branch_outlet_id.company_branch_id', store=True, tracking=True)

    overtime_hours = fields.Float(default=0.0, string='Overtime Hours', tracking=True)
    late_hour = fields.Float(default=0.0, string='Late Hours', tracking=True)

    state = fields.Selection(selection_add=[('submitted_to_manager', 'Submitted To Manager'),
                                            ('submitted_to_finance', 'Submitted To Finance'),
                                            ('cancel', 'Cancel'),
                                            ], tracking=True)


    hours_per_day_rc = fields.Float(related ='contract_id.resource_calendar_id.hours_per_day', tracking=True)
    credit_note = fields.Boolean(string='Credit Note', readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 help="Indicates this payslip has a refund of another", tracking=True)
    contract_id = fields.Many2one('hr.contract', string='Contract', readonly=True,
        states={'draft': [('readonly', False)]}, tracking=True)
    struct_id = fields.Many2one('hr.payroll.structure', string='Structure',
                                readonly=True, states={'draft': [('readonly', False)]},
                                help='Defines the rules that have to be applied to this payslip, accordingly '
                                     'to the contract chosen. If you let empty the field contract, this field isn\'t '
                                     'mandatory anymore and thus the rules applied will be all the rules set on the '
                                     'structure of all contracts of the employee valid for the chosen period', tracking=True)
    name = fields.Char(string='Payslip Name', readonly=True,
        states={'draft': [('readonly', False)]}, tracking=True)
    number = fields.Char(string='Reference', readonly=True, copy=False,
        states={'draft': [('readonly', False)]}, tracking=True)
    date_from = fields.Date(string='Date From', readonly=True, required=True,
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
                            states={'draft': [('readonly', False)]}, tracking=True)
    date_to = fields.Date(string='Date To', readonly=True, required=True,
        default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),
        states={'draft': [('readonly', False)]}, tracking=True)
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batches', readonly=True,
        copy=False, states={'draft': [('readonly', False)]}, tracking=True)
    paid = fields.Boolean(string='Made Payment Order ? ', readonly=True, copy=False,
                          states={'draft': [('readonly', False)]}, tracking=True)
    line_ids = fields.One2many('hr.payslip.line', 'slip_id', string='Payslip Lines', readonly=True,
        states={'draft': [('readonly', False)]}, tracking=True)
    date = fields.Date('Date Account', states={'draft': [('readonly', False)]}, readonly=True,
                       help="Keep empty to use the period of the validation(Payslip) date.", tracking=True)
    journal_id = fields.Many2one('account.journal', 'Salary Journal', readonly=True, required=True,
                                 states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['account.journal'].search([('type', '=', 'general')],
                                                                                         limit=1), tracking=True)
    move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False, tracking=True)

    deduction_amount = fields.Float(string="Deducted Amount")

    def submit_to_manager(self):
        if self.state == 'draft':
            self.state = 'submitted_to_manager'

    def submit_to_finance(self):
        if self.state == 'submitted_to_manager':
            self.state = 'submitted_to_finance'

    def cancel_payslip(self):
        self.move_id.sudo().button_cancel()
        self.move_id.sudo().unlink()
        self.state = 'cancel'

    @api.depends('employee_id','date_from','date_to')
    def _compute_branch_outlet_id(self):
        for rec in self:
            history_branch = self.env['employee.branch.history'].search(
                    [('from_date', '<=', rec.date_from),
                    ('from_date', '<=', rec.date_to),
                    '&',
                    ('to_date', '>=', rec.date_from),
                    ('to_date', '>=', rec.date_to),
                     ('employee_id', '=', rec.employee_id.id)], limit=1)
            if history_branch:
                rec.branch_outlet_id = history_branch.prev_outlet_id or False
            else:
                rec.branch_outlet_id = rec.employee_id.branch_outlet_id or False


    def check_duplicate_record(self):
        for rec in self:
            clause_1 = ['&', ('date_to', '<=', rec.date_to), ('date_to', '>=', rec.date_from)]
            clause_2 = ['&', ('date_from', '<=', rec.date_to), ('date_from', '>=', rec.date_from)]
            clause_3 = ['&', ('date_from', '<=', rec.date_from), '|', ('date_to', '=', False), ('date_to', '>=', rec.date_to)]
            clause_final = [('employee_id', '=', rec.employee_id.id), ('state', '=', 'done'), ('id', '!=', rec.id), '|', '|'] + clause_1 + clause_2 + clause_3
            rec_ids = self.search(clause_final)
            if len(rec_ids) % 2 == 0 and rec.credit_note:
                raise ValidationError(_('You already Refund payslip with same duration of "%s".Kindly check Once.'
                                        % (rec.employee_id.name + ' ' + rec.employee_id.last_name if rec.employee_id.last_name else '')))
            elif not len(rec_ids) % 2 == 0 and not rec.credit_note:
               raise ValidationError(_('You already generated payslip with same duration of "%s".Kindly check Once.'
                                        % (rec.employee_id.name + ' ' + rec.employee_id.last_name if rec.employee_id.last_name else '')))

    def action_payslip_done(self):
        self.check_duplicate_record()
        return super(HrPayslip, self).action_payslip_done()

    def _get_payment_days(self):
        for line in self:
            nb_of_days = (line.date_to - line.date_from).days + 1
            # We will set it to 30 as our calculation is based on 30 days for your company
            month = line.date_from.month
            line.payment_days_org = nb_of_days
            if nb_of_days > 30 or month == 2:
                nb_of_days = 30
            line.payment_days = nb_of_days

    payment_days = fields.Float(compute='_get_payment_days', string='Payment Day(s)', tracking=True)
    payment_days_org = fields.Float(compute='_get_payment_days', string='Payment Day(s)', tracking=True)

    def get_other_allowance_deduction(self, employee_id, date_from, date_to):
        # from_date = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT)
        # to_date = datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT)
        # new_from_date = date_from + relativedelta(months=-1, day=25)
        # last_day = calendar.monthrange(date_to.year, date_to.month)[1]
        # new_to_date = date_to + relativedelta(day=24)
        # if date_to.day < last_day:
        #     new_to_date = date_to
        domain = [('employee_id', '=', employee_id.id),
                  ('payslip_id', '=', False), ('state', 'in', ['done']),
                  ('date', '>=', date_from), ('date', '<=', date_to)]
        other_ids = self.env['other.hr.payslip'].search(domain)
        return other_ids

    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):
        # res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
        res = []
        alw_no_of_days = alw_no_of_hours = alw_percentage = alw_amt = 0.0
        ded_no_of_days = ded_no_of_hours = ded_percentage = ded_amt = 0.0
        for contract in contract_ids:
            other_ids = self.get_other_allowance_deduction(contract.employee_id, date_from, date_to)
            input_deduction_lines = {}
            input_allowance_lines = {}
            if other_ids:
                for other in other_ids:
                    if other.operation_type == 'allowance':
                        if other.calc_type == 'amount':
                            alw_amt += other.amount
                            if 'OTHER_ALLOWANCE_AMOUNT' not in input_allowance_lines:
                                input_allowance_lines['OTHER_ALLOWANCE_AMOUNT'] = alw_amt
                            else:
                                input_allowance_lines.update({'OTHER_ALLOWANCE_AMOUNT': alw_amt})
                        elif other.calc_type == 'days':
                            alw_no_of_days += other.no_of_days
                            if 'OTHER_ALLOWANCE_DAYS' not in input_allowance_lines:
                                input_allowance_lines['OTHER_ALLOWANCE_DAYS'] = alw_no_of_days
                            else:
                                input_allowance_lines.update({'OTHER_ALLOWANCE_DAYS': alw_no_of_days})
                        elif other.calc_type == 'hours':
                            alw_no_of_hours += other.no_of_hours
                            if 'OTHER_ALLOWANCE_HOURS' not in input_allowance_lines:
                                input_allowance_lines['OTHER_ALLOWANCE_HOURS'] = alw_no_of_hours
                            else:
                                input_allowance_lines.update({'OTHER_ALLOWANCE_HOURS': alw_no_of_hours})
                        elif other.calc_type == 'percentage':
                            alw_percentage += other.percentage
                            if 'OTHER_ALLOWANCE_PERCENTAGE' not in input_allowance_lines:
                                input_allowance_lines['OTHER_ALLOWANCE_PERCENTAGE'] = alw_percentage
                            else:
                                input_allowance_lines.update({'OTHER_ALLOWANCE_PERCENTAGE': alw_percentage})

                    elif other.operation_type == 'deduction':
                        if other.calc_type == 'amount':
                            ded_amt += other.amount
                            if 'OTHER_DEDUCTION_AMOUNT' not in input_deduction_lines:
                                input_deduction_lines['OTHER_DEDUCTION_AMOUNT'] = ded_amt
                            else:
                                input_deduction_lines.update({'OTHER_DEDUCTION_AMOUNT': ded_amt})
                        elif other.calc_type == 'days':
                            ded_no_of_days += other.no_of_days
                            if 'OTHER_DEDUCTION_DAYS' not in input_deduction_lines:
                                input_deduction_lines['OTHER_DEDUCTION_DAYS'] = ded_no_of_days
                            else:
                                input_deduction_lines.update({'OTHER_DEDUCTION_DAYS': ded_no_of_days})
                        elif other.calc_type == 'hours':
                            ded_no_of_hours += other.no_of_hours
                            if 'OTHER_DEDUCTION_HOURS' not in input_deduction_lines:
                                input_deduction_lines['OTHER_DEDUCTION_HOURS'] = ded_no_of_hours
                            else:
                                input_deduction_lines.update({'OTHER_DEDUCTION_HOURS': ded_no_of_hours})
                        elif other.calc_type == 'percentage':
                            ded_percentage += other.percentage
                            if 'OTHER_DEDUCTION_PERCENTAGE' not in input_deduction_lines:
                                input_deduction_lines['OTHER_DEDUCTION_PERCENTAGE'] = ded_percentage
                            else:
                                input_deduction_lines.update({'OTHER_DEDUCTION_PERCENTAGE': ded_percentage})

                input_type = self.env['hr.payslip.input.type'].search([('struct_ids', 'in', self.struct_id.id)], limit=1)
                for code, amount in input_allowance_lines.items():
                    res.append({'name': 'Other Allowance',
                                'code': code,
                                'amount': amount,
                                'input_type_id': input_type.id,
                                'contract_id': contract.id})

                for code, amount in input_deduction_lines.items():
                    res.append({'name': 'Other Deduction',
                                'code': code,
                                'amount': amount,
                                'input_type_id': input_type.id,
                                'contract_id': contract.id})
        return res


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection(selection_add=[('submitted_to_manager', 'Submitted To Manager'),
                                            ('submitted_to_finance', 'Submitted To Finance'),
                                            ('cancel', 'Cancel'),
                                            ], tracking=True)


    def submit_to_manager(self):
        if self.state == 'draft':
            self.state = 'submitted_to_manager'

    def submit_to_finance(self):
        if self.state == 'submitted_to_manager':
            self.state = 'submitted_to_finance'

    def cancel_payslip(self):
        for slip in self.slip_ids:
            slip.move_id.sudo().button_cancel()
            slip.move_id.sudo().unlink()
            slip.state = 'cancel'
        self.state = 'cancel'

    def compute_payslip(self):
        for slip in self.slip_ids:
            slip.compute_sheet()

    def unlink(self):
        if any(self.filtered(lambda payslip: payslip.state not in ('draft', 'cancel'))):
            raise UserError(
                _("You can only delete slips in draft/cancel state."))
        return super(HrPayslipRun, self).unlink()


class HrPayslipEmployeesInherit(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        res = super(HrPayslipEmployeesInherit, self).compute_sheet()
        context = dict(self.env.context)
        active_id = self.env['hr.payslip.run'].browse(context.get('active_id'))
        if active_id:
            for slip in active_id.slip_ids:
                slip.compute_sheet()
        return res

