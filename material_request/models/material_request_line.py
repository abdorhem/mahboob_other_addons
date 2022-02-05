# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import Warning, UserError


class MaterialRequestLine(models.Model):
    _name = 'material.request.line'
    _description = 'Material Request Line'

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
    )
    description = fields.Char(
        string='Description',
        required=True,
    )
    qty = fields.Float(
        string='Quantity',
        default=1,
        required=True,
        digits=(16, 4)
    )
    uom_id = fields.Many2one(
        'uom.uom',
        related='product_id.uom_id',
        string='Unit of Measure',
    )
    remark = fields.Char(string='Remark')
    request_id = fields.Many2one('material.request')
    accepted_qty = fields.Char(string='Accepted Quantity')
    src_onhand_qty = fields.Float(string="Source Onhand Stock",
                              compute='_compute_onhand_qty', store=True)
    onhand_qty = fields.Float(string="Onhand STK",
                              compute='_compute_onhand_qty', store=True)
    partner_id = fields.Many2many('res.partner', string="Vendor")

    @api.depends('product_id', 'request_id.branch_outlet_id', 'request_id.source_outlet_id')
    def _compute_onhand_qty(self):
        # Method to get onhand quantity in purchase order line
        for line in self:
            if line.product_id and line.request_id.branch_outlet_id:
                quantity = 0
                location_dest_id = \
                    line.request_id.branch_outlet_id.warehouse_id.lot_stock_id
                quant_recs = self.env['stock.quant'].search(
                    [('product_id', '=', line.product_id.id),
                     ('location_id', '=', location_dest_id.id)])
                for quant_rec in quant_recs:
                    quantity += quant_rec.quantity
                line.onhand_qty = quantity
            if line.product_id and line.request_id.source_outlet_id:
                src_quantity = 0
                location_src_id = \
                    line.request_id.source_outlet_id.warehouse_id.lot_stock_id
                quant_recss = self.env['stock.quant'].search(
                    [('product_id', '=', line.product_id.id),
                     ('location_id', '=', location_src_id.id)])
                for quant_rec in quant_recss:
                    src_quantity += quant_rec.quantity
                line.src_onhand_qty = src_quantity


    # @api.multi
    # @api.onchange('product_id')
    # def product_id_change(self):
    #     if not self.product_id:
    #         return {'domain': {'product_uom': []}}

    #     # remove the is_custom values that don't belong to this template
    #     for pacv in self.product_custom_attribute_value_ids:
    #         if pacv.attribute_value_id not in self.product_id.product_tmpl_id._get_valid_product_attribute_values():
    #             self.product_custom_attribute_value_ids -= pacv

    #     # remove the no_variant attributes that don't belong to this template
    #     for ptav in self.product_no_variant_attribute_value_ids:
    #         if ptav.product_attribute_value_id not in self.product_id.product_tmpl_id._get_valid_product_attribute_values():
    #             self.product_no_variant_attribute_value_ids -= ptav

    #     vals = {}
    #     domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
    #     if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
    #         vals['product_uom'] = self.product_id.uom_id
    #         vals['product_uom_qty'] = self.product_uom_qty or 1.0

    #     product = self.product_id.with_context(
    #         lang=self.order_id.partner_id.lang,
    #         partner=self.order_id.partner_id,
    #         quantity=vals.get('product_uom_qty') or self.product_uom_qty,
    #         date=self.order_id.date_order,
    #         pricelist=self.order_id.pricelist_id.id,
    #         uom=self.product_uom.id
    #     )

    #     result = {'domain': domain}

    #     name = self.get_sale_order_line_multiline_description_sale(product)

    #     vals.update(name=name)

    #     self._compute_tax_id()

    #     if self.order_id.pricelist_id and self.order_id.partner_id:
    #         vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
    #     self.update(vals)

    #     title = False
    #     message = False
    #     warning = {}
    #     if product.sale_line_warn != 'no-message':
    #         title = _("Warning for %s") % product.name
    #         message = product.sale_line_warn_msg
    #         warning['title'] = title
    #         warning['message'] = message
    #         result = {'warning': warning}
    #         if product.sale_line_warn == 'block':
    #             self.product_id = False

    #     return result

    # def get_sale_order_line_multiline_description_sale(self, product):
    #     """ Compute a default multiline description for this sales order line.
    #     This method exists so it can be overridden in other modules to change how the default name is computed.
    #     In general only the product is used to compute the name, and this method would not be necessary (we could directly override the method in product).
    #     BUT in event_sale we need to know specifically the sales order line as well as the product to generate the name:
    #         the product is not sufficient because we also need to know the event_id and the event_ticket_id (both which belong to the sale order line).
    #     """
    #     return product.get_product_multiline_description_sale() + self._get_sale_order_line_multiline_description_variants()

    # def _get_sale_order_line_multiline_description_variants(self):
    #     """When using no_variant attributes or is_custom values, the product
    #     itself is not sufficient to create the description: we need to add
    #     information about those special attributes and values.

    #     See note about `product_no_variant_attribute_value_ids` above the field
    #     definition: this method is not reliable to recompute the description at
    #     a later time, it should only be used initially.

    #     :return: the description related to special variant attributes/values
    #     :rtype: string
    #     """
    #     name = "\n"

    #     product_attribute_with_is_custom = self.product_custom_attribute_value_ids.mapped('attribute_value_id.attribute_id')

    #     # display the no_variant attributes, except those that are also
    #     # displayed by a custom (avoid duplicate)
    #     for no_variant_attribute_value in self.product_no_variant_attribute_value_ids.filtered(
    #         lambda ptav: ptav.attribute_id not in product_attribute_with_is_custom
    #     ):
    #         name += "\n" + no_variant_attribute_value.attribute_id.name + ': ' + no_variant_attribute_value.name

    #     # display the is_custom values
    #     for pacv in self.product_custom_attribute_value_ids:
    #         name += "\n" + pacv.attribute_value_id.attribute_id.name + \
    #             ': ' + pacv.attribute_value_id.name + \
    #             ': ' + (pacv.custom_value or '').strip()

    #     return name

    @api.onchange('product_id')
    def product_id_change(self):
        if self.product_id:
            self.description = self.product_id.name
            self.uom_id = self.product_id.uom_id
        return
