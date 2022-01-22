# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class account_payment(models.Model):
    _inherit = "account.payment"

    internal_transfer_type = fields.Selection([('a_to_a', 'Account To Account'),
                                               ('j_to_j', 'Journal To Journal'),
                                               ('j_to_a','Journal To Account'),
                                               ('a_to_j','Account To Journal')],string=' Internal Transfer Type',default='a_to_a', tracking=True)
    from_account_id = fields.Many2one('account.account',string="From Account", tracking=True)
    from_account_balance = fields.Float(string='Balance', compute='compute_balance', tracking=True, store=True)
    to_account_id = fields.Many2one('account.account',string="To Account", tracking=True)
    to_account_balance = fields.Float(string='Balance', compute='compute_balance', tracking=True, store=True)
    to_journal_id = fields.Many2one('account.journal',string="To Journal", tracking=True)
    from_journal_id = fields.Many2one('account.journal',string="From Journal", tracking=True)
    src_branch_outlet_id = fields.Many2one(
        'res.branch.outlet',
        string="Source Outlet",
        copy=True,
        default=lambda self: self.env.user.branch_outlet_id.id,
        tracking=True
    )

    @api.depends('from_account_id','to_account_id')
    def compute_balance(self):
        if self.from_account_id:
            self.env.cr.execute("select sum(debit) - sum(credit) from account_move_line where account_id = %s and move_id in (select id from account_move where state = 'posted')" % self.from_account_id.id)
            from_bal = self.env.cr.fetchall()
            self.from_account_balance = from_bal[0][0] if from_bal[0][0] != None else 0.0
        if self.to_account_id:
            self.env.cr.execute("select sum(debit) - sum(credit) from account_move_line where account_id = %s and move_id in (select id from account_move where state = 'posted')" % self.to_account_id.id)
            to_bal = self.env.cr.fetchall()
            self.to_account_balance = to_bal[0][0] if to_bal[0][0] != None else 0.0
        return

    @api.onchange('from_journal_id','to_journal_id')
    def onchange_from_journal_id(self):
        if self.payment_type == 'transfer':
            if self.internal_transfer_type == 'j_to_a':
                self.journal_id = False
                if self.from_journal_id:
                    self.journal_id = self.from_journal_id
            if self.internal_transfer_type == 'a_to_j':
                self.journal_id = False
                if self.to_journal_id:
                    self.journal_id = self.to_journal_id
        return

    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:

            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer.custom'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice.custom'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice.custom'
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_payment_entry(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer' and rec.internal_transfer_type == 'j_to_j':
                transfer_credit_aml = move.line_ids.filtered(lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()

            rec.write({'state': 'posted', 'move_name': move.name})
        return True

    def _create_payment_entry(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
            Return the journal entry.
        """
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)

        move = self.env['account.move'].create(self._get_move_vals())

        #Write line corresponding to invoice payment
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
        counterpart_aml_dict.update({'currency_id': currency_id})
        counterpart_aml_dict.update({'branch_outlet_id': move.branch_outlet_id.id})
        #custom code
        if self.payment_type == 'transfer' and self.internal_transfer_type == 'a_to_a' :
            counterpart_aml_dict.update({'account_id' :self.to_account_id.id,
                                         'journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
                                         'branch_outlet_id': self.branch_outlet_id.id,
                                         })
        if self.payment_type == 'transfer' and self.internal_transfer_type == 'a_to_j' :
            counterpart_aml_dict.update({'account_id' :self.to_journal_id.default_debit_account_id.id })
        if self.payment_type == 'transfer' and self.internal_transfer_type == 'j_to_a' :
            counterpart_aml_dict.update({'account_id' :self.to_account_id.id })
        #custom code
        counterpart_aml = aml_obj.create(counterpart_aml_dict)

        #Reconcile with the invoices
        if self.payment_difference_handling == 'reconcile' and self.payment_difference:
            writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
            debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id)
            writeoff_line['name'] = self.writeoff_label
            writeoff_line['account_id'] = self.writeoff_account_id.id
            writeoff_line['debit'] = debit_wo
            writeoff_line['credit'] = credit_wo
            writeoff_line['amount_currency'] = amount_currency_wo
            writeoff_line['currency_id'] = currency_id
            writeoff_line = aml_obj.create(writeoff_line)
            if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                counterpart_aml['debit'] += credit_wo - debit_wo
            if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                counterpart_aml['credit'] += debit_wo - credit_wo
            counterpart_aml['amount_currency'] -= amount_currency_wo

        #Write counterpart lines
        if not self.currency_id.is_zero(self.amount):
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0
            liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
            liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
            liquidity_aml_dict.update({'branch_outlet_id': move.branch_outlet_id.id})

            #custom code
            if self.payment_type == 'transfer' and self.internal_transfer_type == 'a_to_a' :
                liquidity_aml_dict.update({'account_id' :self.from_account_id.id,
                                           'branch_outlet_id':self.src_branch_outlet_id.id,
                                           })
            if self.payment_type == 'transfer' and self.internal_transfer_type == 'j_to_a' :
                liquidity_aml_dict.update({'account_id' :self.from_journal_id.default_credit_account_id.id })

            if self.payment_type == 'transfer' and self.internal_transfer_type == 'a_to_j' :
                liquidity_aml_dict.update({'account_id' :self.from_account_id.id })
            #custom code
            aml_obj.create(liquidity_aml_dict)
            if self.account_payment != 0.0:
                if self.tax_id:
                    amount_with_tax = (self.account_payment * self.tax_id.amount) / 100
                    payment_data_debit = {'payment_id': self.id, 'name': move.ref, 'debit': round(amount_with_tax, 4),
                                          'account_id': self.tax_id.account_id.id, 'date_maturity': move.date,
                                          'partner_id': self.partner_id.id, 'amount': self.account_payment,
                                          'journal_id': self.journal_id.id, 'date': self.payment_date,
                                          'move_id': move.id, 'payment_method_id': self.payment_method_id.id,'branch_outlet_id':self.branch_outlet_id.id}
                    payment_data_credit = {'payment_id': self.id, 'name': self.name, 'credit': round(amount_with_tax, 4) + self.account_payment,
                                           'account_id': self.journal_id.default_credit_account_id.id,
                                           'date_maturity': move.date, 'partner_id': self.partner_id.id,
                                           'amount': self.account_payment, 'journal_id': self.journal_id.id,
                                           'date': self.payment_date, 'move_id': move.id,
                                           'payment_method_id': self.payment_method_id.id,'branch_outlet_id':self.branch_outlet_id.id}
                    payment_data_credit_tax = {'payment_id': self.id, 'name': move.ref,
                                               'debit': self.account_payment,
                                               'account_id': self.journal_id.default_bank_account_id.id,
                                               'date_maturity': move.date, 'partner_id': self.partner_id.id,
                                               'amount': self.account_payment, 'journal_id': self.journal_id.id,
                                               'date': self.payment_date, 'move_id': move.id,
                                               'payment_method_id': self.payment_method_id.id,'branch_outlet_id':self.branch_outlet_id.id}

                    aml_obj.create(payment_data_debit)
                    aml_obj.create(payment_data_credit)
                    aml_obj.create(payment_data_credit_tax)
                else:
                    payment_data_debit = {'payment_id': self.id, 'name': move.ref, 'debit': self.account_payment,
                                          'account_id': self.journal_id.default_bank_account_id.id,
                                          'date_maturity': move.date, 'partner_id': self.partner_id.id,
                                          'amount': self.account_payment, 'journal_id': self.journal_id.id,
                                          'date': self.payment_date, 'move_id': move.id,
                                          'payment_method_id': self.payment_method_id.id,'branch_outlet_id':self.branch_outlet_id.id}
                    payment_data_credit = {'payment_id': self.id, 'name': self.name, 'credit': self.account_payment,
                                           'account_id': self.journal_id.default_credit_account_id.id,
                                           'date_maturity': move.date, 'partner_id': self.partner_id.id,
                                           'amount': self.account_payment, 'journal_id': self.journal_id.id,
                                           'date': self.payment_date, 'move_id': move.id,
                                           'payment_method_id': self.payment_method_id.id,'branch_outlet_id':self.branch_outlet_id.id}
                    aml_obj.create(payment_data_debit)
                    aml_obj.create(payment_data_credit)
        #validate the payment
        if not self.journal_id.post_at_bank_rec:
            move.post()


        #reconcile the invoice receivable/payable line(s) with the payment
        if self.invoice_ids:
            self.invoice_ids.register_payment(counterpart_aml)
        if self.payment_type == 'transfer' and self.internal_transfer_type == 'a_to_a':
            move.journal_id = self.env['account.journal'].search([('type', '=', 'general')], limit=1).id

        return move

    def _synchronize_from_moves(self, changed_fields):
        if self.payment_type == 'transfer':
            return True
        return super(account_payment, self)._synchronize_from_moves(changed_fields)

    def _prepare_move_line_liquidity_vals(self, liquidity_name):
        vals_list = super(
            account_payment, self
        )._prepare_move_line_liquidity_vals(liquidity_name)

        if self.payment_type != 'transfer':
            return vals_list

        for val in vals_list:
            val.update({'branch_outlet_id': self.branch_outlet_id.id})
            if self.internal_transfer_type == 'a_to_a' :
                val.update({
                    'account_id': self.from_account_id.id,
                })
            elif self.internal_transfer_type == 'j_to_a' :
                val.update({
                    'account_id' :self.from_journal_id.default_account_id.id
                })
            elif self.internal_transfer_type == 'a_to_j' :
                val.update({
                    'account_id' :self.from_account_id.id
                })
            elif self.internal_transfer_type == 'j_to_j' :
                val.update({
                    'account_id' :self.from_journal_id.default_account_id.id
                })

        return vals_list

    def _prepare_move_line_receivable_payable_vals(self, receivalble_vals):
        vals_list = super(account_payment, self)._prepare_move_line_receivable_payable_vals(receivalble_vals)

        if self.payment_type != 'transfer':
            return vals_list

        for val in vals_list:
            val.update({'branch_outlet_id': self.branch_outlet_id.id})
            if self.internal_transfer_type == 'a_to_a' :
                val.update({
                    'account_id' :self.to_account_id.id,
                    'journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
                })
            elif self.internal_transfer_type == 'a_to_j' :
                val.update({
                    'account_id' :self.to_journal_id.default_account_id.id
                })
            elif self.internal_transfer_type == 'j_to_a' :
                val.update({
                    'account_id' :self.to_account_id.id
                })
            elif self.internal_transfer_type == 'j_to_j' :
                val.update({
                    'account_id' :self.to_journal_id.default_account_id.id
                })
        return vals_list
