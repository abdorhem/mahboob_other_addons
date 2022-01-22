from odoo import api, models, fields, _


class MultiApproval(models.Model):
    _inherit = 'multi.approval'

    create_record_after_approval = fields.Boolean(related="type_id.create_record_after_approval")
    record_to_create = fields.Selection(related="type_id.record_to_create")
    account_payment_ids = fields.One2many("account.payment", "approval_request_id")
    hr_expense_ids = fields.One2many("hr.expense", "approval_request_id")
    purchase_order_ids = fields.One2many("purchase.order", "approval_request_id")
    account_move_ids = fields.One2many("account.move", "approval_request_id")
    last_approve_user_id = fields.Integer(compute="_compute_last_approve_user")
    show_for_current_user = fields.Boolean(compute='get_show_for_current_user')

    def get_show_for_current_user(self):
        current_uid = self.env.context.get('uid', False)
        if current_uid and current_uid == self.last_approve_user_id:
            self.show_for_current_user = True
        else:
            self.show_for_current_user = False

    def view_partner_ledger(self):
        if self.contact_id:
            return self.env['ins.partner.ledger'].create({"partner_ids": [self.contact_id.id]}).action_view()

    def create_record(self):
        action = "account.action_account_payments_payable"
        view = "account.view_account_payment_form"
        if self.record_to_create == 'account.move':
            action = "account.action_move_journal_line"
            view = "account.view_move_form"
        elif self.record_to_create == 'hr.expense':
            action = "hr_expense.action_hr_expense_sheet_all"
            view = "hr_expense.view_hr_expense_sheet_form"
        elif self.record_to_create == 'purchase.order':
            action = "purchase.purchase_form_action"
            view = "purchase.purchase_order_form"
        result = self.env["ir.actions.actions"]._for_xml_id(action)
        res = self.env.ref(view, False)
        form_view = [(res and res.id or False, 'form')]
        if 'views' in result:
            result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
        else:
            result['views'] = form_view
        import ast
        ctx = ast.literal_eval(result['context'])
        ctx["default_approval_request_id"] = self.id
        ctx["default_partner_id"] = self.contact_id.id
        if 'view_no_maturity' in ctx:
            ctx["view_no_maturity"] = True
        result['context'] = str(ctx)
        return result
    
    def _compute_last_approve_user(self):
        if len(self.type_id.line_ids) > 0:
            self.last_approve_user_id = self.type_id.line_ids.sorted(lambda l: l.sequence)[-1].user_id.id
        else:
            self.last_approve_user_id = False
