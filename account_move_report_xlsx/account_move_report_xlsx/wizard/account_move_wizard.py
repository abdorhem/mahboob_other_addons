# -*- coding: utf-8 -*-

import base64
import tempfile
from datetime import datetime

import pytz
import xlsxwriter
from dateutil.relativedelta import relativedelta
from pytz import timezone, UTC

from odoo import fields, models


class AccountMoveHistory(models.TransientModel):
    _name = "account.move.history"
    _description = "Account Move History"

    file = fields.Binary(string="File")
    name = fields.Char(string="Name")


class AccountMoveReportWizard(models.TransientModel):
    _name = "account.move.report.wizard"
    _description = "Account Move Report Wizard"

    start_date = fields.Date(
        string='Start Date', required=True
    )

    end_date = fields.Date(
        string='End Date', required=True
    )

    account_ids = fields.Many2many("account.account", string="Accounts")

    def _get_account_move_data(self):
        account_move = self.env['account.move']
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
            ['Date', 'Journal Name', 'Journal Entry', 'Partner', 'Reference', 'Total']
        ]
        worksheet.write_row("A2:F2", heading[0])
        name = "Journal Entry Report.xlsx"
        st_dt = self.start_date.strftime('%d/%m/%Y')
        end_dt = self.end_date.strftime('%d/%m/%Y')
        worksheet.merge_range(0, 0, 0, 5, ' Date Range: ' + st_dt + ' To ' + end_dt, center)
        lines = self._get_account_move_data()
        colm = 0
        for line in lines:
            row += 1
            worksheet.write(row, colm, line.date)
            worksheet.write(row, colm + 1, line.journal_id.name)
            worksheet.write(row, colm + 2, line.name)
            worksheet.write(row, colm + 3, line.partner_id.name if line.partner_id else "")
            worksheet.write(row, colm + 4, line.ref or "")
            worksheet.write(row, colm + 5, line.amount_total_signed or 0.0)


        worksheet.write(row+1, 4, "TOTAL AMOUNT")
        worksheet.write(row+1, 5, sum(lines.mapped('amount_total_signed')))
        workbook.close()
        data = base64.encodebytes(open(str(temp_location) + '.xlsx', 'rb').read())
        report_id = self.env['account.move.history'].create({'file': data,
                                                             'name': name})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entry Report',
            'res_model': 'account.move.history',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': report_id.id,
            'target': 'new',
        }
