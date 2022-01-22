from odoo import api, models, fields, _


class HRExpense(models.Model):
    _inherit = 'hr.expense'

    approval_request_id = fields.Many2one("multi.approval", "Request")
