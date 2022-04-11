
from odoo import models, fields, api

class POSConfigInherit(models.Model):
    _inherit = 'pos.config'

    allow_qr_code = fields.Boolean(string="Add QR Code in Receipt")


class PosSession(models.Model):
    _inherit = 'pos.session'
    
    def _get_tax_vals(self, key, amount, amount_converted, base_amount_converted):
        account_id, repartition_line_id, tax_id, tag_ids = key
        tax = self.env['account.tax'].browse(tax_id)
        partial_args = {
            'name': tax.name + ('-' + self.branch_outlet_id.name) if self.branch_outlet_id else '',
            'account_id': account_id,
            'move_id': self.move_id.id,
            'tax_base_amount': abs(base_amount_converted),
            'tax_repartition_line_id': repartition_line_id,
            'tax_tag_ids': [(6, 0, tag_ids)],
        }
        return self._debit_amounts(partial_args, amount, amount_converted)
    
