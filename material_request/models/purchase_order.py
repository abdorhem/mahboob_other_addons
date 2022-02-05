from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    custom_request_id = fields.Many2one(
        'material.request',
        string='Material Request',
        copy=False
    )

    custom_picking_id = fields.Many2one('stock.picking', string="Stock Picking")