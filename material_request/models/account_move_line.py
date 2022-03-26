# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full
# copyright and licensing details.

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        lines = super(AccountMoveLine, self).create(vals_list)
        for line in lines:
            if line.move_id.stock_move_id.move_line_ids:
                for move_line in line.move_id.stock_move_id.move_line_ids:
                    group_stock_scrap_id = self.env['group.stock.scrap'].search([('name', '=', move_line.move_id.resource_ref)])
                    if group_stock_scrap_id:
                        line.move_id.date = group_stock_scrap_id.date_expected
        return lines
