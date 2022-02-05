# -*- coding: utf-8 -*-

from odoo import models, fields, api
from lxml import etree


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_outlet(self):
        if self.env.user.outlet_select == 'allow':
            return []
        if self.env.user.outlet_select == 'not_allow':
            return [('id', 'not in', self.env['res.branch.outlet'].search([]).ids)]
        if self.env.user.outlet_select == 'selected_outlet':
            return [('id', 'in', self.env.user.outlet_ids.ids)]

    request_id = fields.Many2one(
        'material.request',
        string='Material Requisition',
        readonly=True,
        copy=True
    )
    src_pick_id = fields.Many2one('stock.picking')
    source_outlet_id = fields.Many2one(
        'res.branch.outlet',
        string="Source Outlet",
        copy=True, domain=_get_outlet
    )
    dest_outlet_id = fields.Many2one(
        'res.branch.outlet',
        string="Destination Outlet",
        copy=True,domain=_get_outlet
    )
    pos_order_id = fields.Many2one('pos.order')
    is_transit_to_dest = fields.Boolean(
        string='Is Transit to Destination',
        compute='_compute_is_transit_to_dest'
    )

    @api.depends('request_id', 'location_id', 'location_dest_id')
    def _compute_is_transit_to_dest(self):
        for picking in self:
            val = False
            if picking.request_id:
                rq_d = picking.request_id.branch_outlet_id.warehouse_id.lot_stock_id
                sp_d = picking.location_dest_id
                if rq_d and sp_d and rq_d.id == sp_d.id:
                    val = True
            picking.is_transit_to_dest = val

    @api.onchange('source_outlet_id')
    def onchange_source_outlet_id(self):
        if self.source_outlet_id:
            self.dest_outlet_id = False
            self.location_id = self.source_outlet_id.warehouse_id.lot_stock_id
            self.picking_type_id = self.source_outlet_id.warehouse_id.int_type_id
        return

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        if self.picking_type_id:
            if self.picking_type_id.default_location_src_id:
                location_id = self.picking_type_id.default_location_src_id.id
            elif self.partner_id:
                location_id = self.partner_id.property_stock_supplier.id
            else:
                customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()

            if self.picking_type_id.code != 'internal':
                if self.picking_type_id.default_location_dest_id:
                    location_dest_id = self.picking_type_id.default_location_dest_id.id
                elif self.partner_id:
                    location_dest_id = self.partner_id.property_stock_customer.id
                else:
                    location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()

                if self.state == 'draft':
                    self.location_id = location_id
                    self.location_dest_id = location_dest_id
            else:
                self.location_dest_id = False
        # TDE CLEANME move into onchange_partner_id
        if self.partner_id and self.partner_id.picking_warn:
            if self.partner_id.picking_warn == 'no-message' and self.partner_id.parent_id:
                partner = self.partner_id.parent_id
            elif self.partner_id.picking_warn not in (
            'no-message', 'block') and self.partner_id.parent_id.picking_warn == 'block':
                partner = self.partner_id.parent_id
            else:
                partner = self.partner_id
            if partner.picking_warn != 'no-message':
                if partner.picking_warn == 'block':
                    self.partner_id = False
                return {'warning': {
                    'title': ("Warning for %s") % partner.name,
                    'message': partner.picking_warn_msg
                }}

    @api.onchange('dest_outlet_id')
    def onchange_dest_outlet_id(self):
        if self.dest_outlet_id:
            self.location_dest_id = self.dest_outlet_id.warehouse_id.lot_stock_id
        return

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        if view_type=='form':
            res = super(StockPicking, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                                   toolbar=toolbar, submenu=submenu)
            dom = etree.XML(res['arch'])
            if self.move_ids_without_package.reserved_availability == self.move_ids_without_package.product_uom_qty:
                for node in dom.xpath("//button[@name='create_po']"):
                    node.set("modifiers", '{"invisible":true}')
            if self.move_ids_without_package.reserved_availability != self.move_ids_without_package.product_uom_qty:
                for node in dom.xpath("//button[@name='create_po']"):
                    node.set("modifiers", '{"invisible":false}')
                res['arch'] = etree.tostring(dom)
            dom = etree.XML(res['arch'])
            if self.env.user.has_group('dwf.group_dwf_creation_restriction_for_trasnfer'):
                for node in dom.xpath("//form[1]"):
                    node.attrib['edit'] = 'false'
                    node.attrib['create'] = 'false'
                res['arch'] = etree.tostring(dom)
        elif view_type=='tree':
            view_id_tree = self.env.ref('stock.vpicktree').id
            res = super(StockPicking, self).fields_view_get(view_id=view_id_tree, view_type=view_type,
                                                            toolbar=toolbar, submenu=submenu)
            dom = etree.XML(res['arch'])
            if self.env.user.has_group('dwf.group_dwf_creation_restriction_for_trasnfer'):
                for node in dom.xpath("//tree[1]"):
                    node.attrib['create'] = 'false'
                res['arch'] = etree.tostring(dom)
        elif view_type=='kanban':
            res = super(StockPicking, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                            toolbar=toolbar, submenu=submenu)
            dom = etree.XML(res['arch'])
            if self.env.user.has_group('dwf.group_dwf_creation_restriction_for_trasnfer'):
                for node in dom.xpath("//kanban[1]"):
                    node.attrib['create'] = 'false'
                res['arch'] = etree.tostring(dom)

        elif view_type=='calendar':
            res = super(StockPicking, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                            toolbar=toolbar, submenu=submenu)
            dom = etree.XML(res['arch'])
            if self.env.user.has_group('dwf.group_dwf_creation_restriction_for_trasnfer'):
                for node in dom.xpath("//calendar[1]"):
                    node.attrib['create'] = 'false'
                res['arch'] = etree.tostring(dom)
        else:
            res = super(StockPicking, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                            toolbar=toolbar, submenu=submenu)
        return res

    def create_po(self):
        ex_order = self.env['purchase.order'].search([('custom_picking_id','=',self.id)])
        form_id = self.env.ref('purchase.purchase_order_form').id
        if ex_order:
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'purchase.order',
                'views': [(form_id, 'form')],
                'view_id': form_id,
                'res_id': ex_order[0].id
            }

        else:
            if self.move_ids_without_package.reserved_availability < self.move_ids_without_package.product_uom_qty:
                order = self.env['purchase.order'].sudo().create({
                    'partner_id':self.env['res.partner'].search([('name', 'ilike', 'internal purchase request')])[0].id if self.env['res.partner'].search([('name', 'ilike', 'internal purchase request')]) else False,
                    'currency_id':self.env.user.company_id.currency_id.id,
                    'date_order':fields.Date.today(),
                    'company_id':self.env.user.company_id.id,
                    'branch_outlet_id': self.source_outlet_id.id,
                    'picking_type_id':self.source_outlet_id.warehouse_id.int_type_id.id,
                    'origin': self.name,
                    'custom_picking_id':self.id,
                    'user_id': self.env.user.id,
                })
                self.env['purchase.order.line'].sudo().create({
                    'product_id': self.move_ids_without_package.product_id.id,
                    'name': self.move_ids_without_package.product_id.name,
                    'product_qty': self.move_ids_without_package.product_uom_qty - self.move_ids_without_package.reserved_availability,
                    'product_uom': self.move_ids_without_package.product_uom.id,
                    'date_planned': fields.Date.today(),
                    'price_unit': self.move_ids_without_package.product_id.lst_price,
                    'order_id': order.id,
                })
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'purchase.order',
                    'views': [(form_id, 'form')],
                    'view_id': form_id,
                    'res_id': order.id
                }

    def action_show_po(self):
        for rec in self:
            purchase_action = self.env.ref('purchase.purchase_rfq')
            purchase_action = purchase_action.read()[0]
            purchase_action['domain'] = str([('custom_picking_id', '=', rec.id)])
        return purchase_action

    
# class StockImmediateTransfer(models.TransientModel):
#     _inherit = 'stock.immediate.transfer'

    def _action_done(self):
#     def process(self):
        res = super(StockPicking, self)._action_done()
        stock_picking_obj = self.env['stock.picking']
        stock_move_obj = self.env['stock.move']

#         pickings_to_validate = self.env.context.get('button_validate_picking_ids')
#         pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate)

        for pick in self:
            if pick.request_id and pick.location_dest_id.usage == 'transit':
                transfer = self.env['stock.picking'].search(
                    [('request_id', '=', pick.request_id.id),
                     ('location_id.usage','=','transit'), ('backorder_id','=',False)], limit=1)
                transit_location = self.env['stock.location'].search([
                    ('usage', '=', 'transit'),
                    ('company_id', '=', pick.company_id.id),
                ], limit=1)
                picking_vals_td = {
                    'location_id': transit_location.id,  # rec.source_outlet_id.warehouse_id.lot_stock_id.id,
                    'location_dest_id': pick.request_id.branch_outlet_id.warehouse_id.lot_stock_id.id,
                    'picking_type_id': self.env['stock.picking.type'].search([('code', '=', 'internal'),
                                                                              ('warehouse_id', '=',
                                                                               pick.request_id.branch_outlet_id.warehouse_id.id)]).id,
                    'branch_outlet_id': pick.request_id.branch_outlet_id.id,
                    'company_branch_id': pick.request_id.company_branch_id.id,
                    'request_id': pick.request_id.id,
                    'origin': pick.request_id.name,
                    'source_outlet_id': pick.request_id.source_outlet_id.id,  # Source Outlet
                    'dest_outlet_id': pick.request_id.branch_outlet_id.id,  # Destination Outlet
                    'company_id': pick.request_id.company_id.id,  # Company
                    'src_pick_id': pick.id
                }
                picking_id_td = stock_picking_obj.sudo().create(picking_vals_td)
                delivery_vals_td = {
                    'delivery_picking_id': picking_id_td.id,
                    'state': 'received'
                }
                pick.request_id.write(delivery_vals_td)
                pick_vals_td =  pick.request_id._prepare_pick_dest_vals_from_src(pick, picking_id_td)
                picking_id_td['move_lines'] = pick_vals_td
                picking_id_td.action_confirm()
                    # stock_move_rec_td = stock_move_obj.sudo().create(pick_vals_td)
        return res
