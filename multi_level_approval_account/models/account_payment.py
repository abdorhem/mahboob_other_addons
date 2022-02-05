from odoo import api, models, fields, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    approval_request_id = fields.Many2one("multi.approval", "Request")
