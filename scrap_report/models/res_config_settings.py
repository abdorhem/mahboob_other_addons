# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    scrap_rec_limit = fields.Integer(string="Records Limit", default=80,
            help="Limit the number of records to display on screen at a time.")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['scrap_rec_limit'] = int(self.env['ir.config_parameter'].sudo().get_param(
                'scrap_report.scrap_rec_limit')) or 80
        return res

    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('scrap_report.scrap_rec_limit',
                self.scrap_rec_limit)
