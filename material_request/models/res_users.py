# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResUers(models.Model):
    _inherit = 'res.users'
    region_id = fields.Many2one('res.country.state', string='Region')
    branch_ids = fields.Many2many('res.branch.outlet',string='Branch')

    @api.onchange('region_id')
    def _onchange_region_id(self):
        return {'domain': {'branch_ids': [('region_id', '=', self.region_id.id)]},
                'value': {'branch_ids': False}}


    