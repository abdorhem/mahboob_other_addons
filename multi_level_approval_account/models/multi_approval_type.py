from odoo import api, models, fields


class MultiApprovalType(models.Model):
    _inherit = 'multi.approval.type'

    create_record_after_approval = fields.Boolean("Create Record After Approval?", default=False)
    record_to_create = fields.Selection([("account.payment", "Manual Payment"),
                                         ("hr.expense", "HR Expense"),
                                         ("purchase.order", "Purchase Order"),
                                         ("account.move", "Journal Entry")])
