# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResUers(models.Model):
    _inherit = 'res.users'
    region_id = fields.Many2one('res.country.state', string='Regsion')
    branch_ids = fields.Many2many('res.branch.outlet', string='Branch')

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    branch_outlet_id = fields.Many2one(
        'res.branch.outlet',
        string="Outlet",
        copy=False,
        default=lambda self: self.env.user.branch_outlet_id.id,
    )
    company_branch_id = fields.Many2one(
        'res.company.branch', string="Company Branch",
        related='branch_outlet_id.company_branch_id', store=True)

    @api.onchange('branch_outlet_id')
    def _onchange_branch_outlet_id(self):
        if self.branch_outlet_id:
            self.location_id = self.branch_outlet_id.warehouse_id.lot_stock_id.id

    def _prepare_move_values(self):
        res = super(StockScrap, self)._prepare_move_values()
        if not res.get('branch_outlet_id'):
            res.update({'branch_outlet_id': self.branch_outlet_id.id,
                        'company_branch_id': self.company_branch_id.id,
                        })
        return res

    def schedular_update_date_scrap_order(self):
        active_ids = self._context.get('active_ids')
        orders = self.browse(active_ids)
        for o in orders:
            for move in o.move_id:
                move.date = o.date_expected
                for account_move in move.account_move_ids:
                    self.env.cr.execute(
                        """UPDATE account_move set date=%s where id=%s""",
                        (o.date_expected,
                         account_move.id))
                    for account_line in account_move.line_ids:
                        self.env.cr.execute(
                            """UPDATE account_move_line set date=%s,date_maturity=%s where id=%s""",
                            (o.date_expected,
                             o.date_expected,
                             account_line.id))
                for move_line in move.move_line_ids:
                    move_line.date = move_line.move_id.date
                    # self.env.cr.execute(
                    #     """UPDATE product_price_history set datetime=%s where product_id=%s""",
                    #     (mo.date_planned_start, move_line.product_id.id))
