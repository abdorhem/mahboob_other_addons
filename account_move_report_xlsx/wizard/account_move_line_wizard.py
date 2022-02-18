# -*- coding: utf-8 -*-

import base64
import tempfile
from datetime import datetime

import pytz
import xlsxwriter
from dateutil.relativedelta import relativedelta
from pytz import timezone, UTC

from odoo import fields, models


class AccountMoveLineHistory(models.TransientModel):
    _name = "account.move.line.history"
    _description = "Account Move Line History"

    file = fields.Binary(string="File")
    name = fields.Char(string="Name")


class AccountMoveLineReportWizard(models.TransientModel):
    _name = "account.move.line.report.wizard"
    _description = "Account Move Line Report Wizard"

    start_date = fields.Date(
        string='Start Date', required=True
    )

    end_date = fields.Date(
        string='End Date', required=True
    )

    account_ids = fields.Many2many("account.account", string="Accounts")

    def _get_account_move_data(self):
        account_move = self.env['account.move.line']
        domain = [('date', '>=', self.start_date),
                  ('date', '<=', self.end_date)]
        if len(self.account_ids) > 0:
            domain.append(('account_id', 'in', self.account_ids.ids))
        data = account_move.search(domain)
        return data

    def generate_report(self):
        temp_location = tempfile.mkstemp()[1]
        workbook = xlsxwriter.Workbook(str(temp_location) + '.xlsx')
        worksheet = workbook.add_worksheet()
        worksheet.set_column("A:F", 20)
        center = workbook.add_format({'align': 'center'})
        row = 1
        heading = [
            ['Date', 'Journal Name', 'Journal Entry', 'Partner', 'Reference', 'Account', 'Debit', 'Credit']
        ]
        worksheet.write_row("A2:F2", heading[0])
        name = "Journal Entry Details Report.xlsx"
        st_dt = self.start_date.strftime('%d/%m/%Y')
        end_dt = self.end_date.strftime('%d/%m/%Y')
        worksheet.merge_range(0, 0, 0, 7, ' Date Range: ' + st_dt + ' To ' + end_dt, center)
        lines = self._get_account_move_data()
        colm = 0
        for line in lines:
            row += 1
            worksheet.write(row, colm, line.date)
            worksheet.write(row, colm + 1, line.move_id.journal_id.name)
            worksheet.write(row, colm + 2, line.move_id.name)
            worksheet.write(row, colm + 3, line.partner_id.name if line.partner_id else "")
            worksheet.write(row, colm + 4, line.ref or "")
            worksheet.write(row, colm + 5, line.account_id.name or "")
            worksheet.write(row, colm + 6, line.debit or 0.0)
            worksheet.write(row, colm + 7, line.credit or 0.0)

        workbook.close()
        data = base64.encodebytes(open(str(temp_location) + '.xlsx', 'rb').read())
        report_id = self.env['account.move.line.history'].create({'file': data,
                                                                  'name': name})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entry Details Report',
            'res_model': 'account.move.line.history',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': report_id.id,
            'target': 'new',
        }
