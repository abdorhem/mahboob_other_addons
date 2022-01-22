from odoo import api, models, fields, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    approval_request_id = fields.Many2one("multi.approval", "Request")
