from odoo import models, fields, api, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    custom_request_id = fields.Many2one(
        'material.request',
        string='Material Request',
        copy=False
    )
