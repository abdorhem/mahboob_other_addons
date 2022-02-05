# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError


class MaterialRequest(models.Model):
    _name = 'material.request'
    _description = 'Material  Request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'id desc'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """
            Override method for remove Make Recurring AccountInvoice
        """
        view_id_form = self.env.ref('material_request.material_request_form_view').id
        view_id_tree = self.env.ref('material_request.material_request_tree_view').id
        if view_type == 'form':
            res = super(MaterialRequest, self).fields_view_get(
                view_id=view_id_form, view_type=view_type, toolbar=toolbar, submenu=submenu)
            dom = etree.XML(res['arch'])
            for node in dom.xpath("//button[@name='action_cancel']"):
                if self.env.user.has_group('material_request.group_dwf_material_req_cancel'):
                    node.set("modifiers", '{"invisible":false}')
            for node in dom.xpath("//div[@class='oe_button_box']"):
                if self.env.user.has_group('dwf.group_dwf_hide_picking_from_material_request'):
                    node.set("modifiers", '{"invisible":true}')

            res['arch'] = etree.tostring(dom)
        else:
            res = super(MaterialRequest, self).fields_view_get(
                view_id=view_id_tree, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return res

    name = fields.Char(
        string='Number',
        index=True,
        readonly=1,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('received', 'Received'),
        ('reject', 'Rejected')],
        tracking=True, default='draft'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Requested By',
        default=lambda self: self.env.user and self.env.user.id or False,
        required=True,
        copy=True,
    )
    request_action = fields.Selection([('internal_picking', 'Internal Picking'), ('purchase_order', 'Purchase Order')])
    request_date = fields.Date(string='Request Date', default=date.today())
    request_line_ids = fields.One2many('material.request.line', 'request_id',
        string='Request', copy=True)
    source_outlet_id = fields.Many2one('res.branch.outlet', string='Source Outlet')
    branch_outlet_id = fields.Many2one('res.branch.outlet', string='Destination Outlet')
    company_branch_id = fields.Many2one('res.company.branch', string='Company Branch',
        related='branch_outlet_id.company_branch_id')
    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Picking Type',
        copy=True,
    )
    delivery_picking_id = fields.Many2one(
        'stock.picking',
        string='Internal Picking',
        readonly=True,
        copy=True,
    )
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id, readonly=True)
    transfer_count = fields.Integer(compute='_compute_transfer_count', string='Transfer Count')

    @api.onchange('request_date')
    def onchange_request_date(self):
        if self.env.user.has_group('dwf.group_dwf_date_restriction'):
            if self.request_date:
                if self.request_date < (datetime.today().date() - relativedelta(days=self.env.user.restricted_dates)):
                    self.request_date = False
            if self.request_date:
                if self.request_date > (datetime.today().date() + relativedelta(days=self.env.user.restricted_dates)):
                    self.request_date = False

    def _compute_transfer_count(self):
        # retrieve all related transfer count
        picking = self.env['stock.picking'].search(
                                                   [('request_id', '=', self.id)])
        count = 0
        for pick in picking:
            count += 1
        self.transfer_count = count

    def action_reset_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def action_confirm(self):
        for rec in self:
            if any(req.product_id.variant_bom_ids[0].type == 'normal' for req in rec.request_line_ids if req.product_id.variant_bom_ids):
                bom_pro_lst = [req.id for req in rec.request_line_ids if req.product_id.variant_bom_ids if
                               req.product_id.variant_bom_ids[0].type == 'normal']
                prod_lst = (list(set(rec.request_line_ids.ids).symmetric_difference(set(bom_pro_lst))))

                return {
                    'name': _("Create Mo"),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'create.mo.wiz',
                    'target': 'new',
                    'type': 'ir.actions.act_window',
                    'context': {'mo_rec':rec,
                                'prod_lst':prod_lst},
                }
            else:
                if not rec.source_outlet_id.warehouse_id:
                    raise UserError(_('Please Select Warehouse for Source Outlet.'))
                elif not rec.branch_outlet_id.warehouse_id:
                    raise UserError(_('Please Select Warehouse for Destination Outlet'))
                else:
                    rec.write({'state': 'confirm'})
                    rec.action_approve()

    @api.model
    def _prepare_pick_vals(self, line=False, stock_id=False):
        """ This method is used to create stock moves from picking."""
        transit_location = self.env['stock.location'].search([
            ('usage', '=', 'transit'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        pick_vals = {
            'product_id': line.product_id.id,
            'product_uom_qty': line.qty,
            'product_uom': line.uom_id.id,
            'location_id': self.source_outlet_id.warehouse_id.lot_stock_id.id,
            'location_dest_id': transit_location.id,
            'name': line.product_id.name,
            'picking_type_id': self.picking_type_id.id,
            'picking_id': stock_id.id,
            'branch_outlet_id': self.branch_outlet_id.id,
            'company_id': self.company_id.id,
            'value':line.product_id.standard_price * line.qty,
        }
        return pick_vals
    def _prepare_pick_dest_vals(self, line=False, stock_id=False):
        """ This method is used to create stock moves from picking."""
        transit_location = self.env['stock.location'].search([
            ('usage', '=', 'transit'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        pick_vals = {
            'product_id': line.product_id.id,
            'product_uom_qty': line.qty,
            'product_uom': line.uom_id.id,
            'location_id': transit_location.id,
            'location_dest_id':  self.branch_outlet_id.warehouse_id.lot_stock_id.id,
            'name': line.product_id.name,
            'picking_type_id': self.picking_type_id.id,
            'picking_id': stock_id.id,
            'branch_outlet_id': self.branch_outlet_id.id,
            'company_id': self.company_id.id,
            'value': line.product_id.standard_price * line.qty,
        }
        return pick_vals

    def action_approve(self):
        """ This method is used to create Internal Transfer."""
        for rec in self:
            rec.write({'state': 'approve'})
        stock_picking_obj = self.env['stock.picking']
        stock_move_obj = self.env['stock.move']
        po_dict = {}
        transfer_dict = {}
        purchase_line_obj = self.env['purchase.order.line']
        purchase_obj = self.env['purchase.order']
        for rec in self:
            if not rec.request_line_ids:
                raise Warning(_('Please create some requisition lines.'))
            for line in rec.request_line_ids:
                if rec.request_action == 'internal_picking':
                    picking_st = 'picking_st'
                    location_dest = ''
                    picking_td = 'picking_td'
                    if picking_st not in transfer_dict:
                        transit_location = self.env['stock.location'].search([
                                                                            ('usage','=', 'transit'),
                                                                            ('company_id','=', self.company_id.id),
                                                                            ],limit=1)
                        picking_vals_st = {
                            'location_id': rec.source_outlet_id.warehouse_id.lot_stock_id.id,
                            'location_dest_id': transit_location.id, #rec.branch_outlet_id.warehouse_id.lot_stock_id.id,
                            'picking_type_id': self.env['stock.picking.type'].search([('code', '=', 'internal'),('warehouse_id', '=', self.source_outlet_id.warehouse_id.id)]).id,
                            'branch_outlet_id': rec.branch_outlet_id.id,
                            'company_branch_id': rec.company_branch_id.id,
                            'request_id': rec.id,
                            'origin': rec.name,
                            'source_outlet_id': rec.source_outlet_id.id,  # Source Outlet
                            'dest_outlet_id': rec.branch_outlet_id.id,  # Destination Outlet
                            'company_id': rec.company_id.id,  # Company
                        }
                        picking_vals_td = {
                            'location_id': transit_location.id, #rec.source_outlet_id.warehouse_id.lot_stock_id.id,
                            'location_dest_id': rec.branch_outlet_id.warehouse_id.lot_stock_id.id,
                            'picking_type_id': self.env['stock.picking.type'].search([('code', '=', 'internal'),
                                ('warehouse_id', '=', rec.branch_outlet_id.warehouse_id.id)]).id,
                            'branch_outlet_id': rec.branch_outlet_id.id,
                            'company_branch_id': rec.company_branch_id.id,
                            'request_id': rec.id,
                            'origin': rec.name,
                            'source_outlet_id': rec.source_outlet_id.id,  # Source Outlet
                            'dest_outlet_id': rec.branch_outlet_id.id,  # Destination Outlet
                            'company_id': rec.company_id.id,  # Company
                        }
                        picking_id_st = stock_picking_obj.sudo().create(picking_vals_st)
                        # picking_id_td = stock_picking_obj.sudo().create(picking_vals_td)
                        transfer_dict.update({picking_st: picking_id_st,
                                              # picking_td: picking_id_td
                                              })
                        delivery_vals_st = {
                            'delivery_picking_id': picking_id_st.id,
                            'state': 'received'
                        }
                        # delivery_vals_td = {
                        #     'delivery_picking_id': picking_id_td.id,
                        #     'state': 'received'
                        # }
                        rec.write(delivery_vals_st)
                        # rec.write(delivery_vals_td)
                        pick_vals_st = rec._prepare_pick_vals(line, picking_id_st)
                        pick_vals_st.update({'picking_type_id':self.env['stock.picking.type'].search([('code', '=', 'internal'),
                                ('warehouse_id', '=', rec.source_outlet_id.warehouse_id.id)]).id})
                        # pick_vals_td = rec._prepare_pick_dest_vals(line, picking_id_td)
                        # pick_vals_td.update(
                        #     {'picking_type_id': self.env['stock.picking.type'].search([('code', '=', 'internal'),
                        #                                                                ('warehouse_id', '=',
                        #                                                                 rec.branch_outlet_id.warehouse_id.id)]).id})
                        stock_move_rec_st = stock_move_obj.sudo().create(pick_vals_st)
                        # stock_move_rec_td = stock_move_obj.sudo().create(pick_vals_td)

                        if picking_id_st:
                            picking_id_st.action_confirm()
                    else:
                        picking_id_st = transfer_dict.get(picking_st)
                        # picking_id_td = transfer_dict.get(picking_td)
                        pick_vals_st = rec._prepare_pick_vals(line, picking_id_st)
                        # pick_vals_td = rec._prepare_pick_dest_vals(line, picking_id_td)
                        pick_vals_st.update(
                            {'picking_type_id': self.env['stock.picking.type'].search([('code', '=', 'internal'),
                                                                                       ('warehouse_id', '=',
                                                                                        rec.source_outlet_id.warehouse_id.id)]).id})
                        # pick_vals_td.update(
                        #     {'picking_type_id': self.env['stock.picking.type'].search([('code', '=', 'internal'),
                        #                                                                ('warehouse_id', '=',
                        #                                                                 rec.branch_outlet_id.warehouse_id.id)]).id})
                        stock_move_rec_st = stock_move_obj.sudo().create(pick_vals_st)
                        # stock_move_rec_td = stock_move_obj.sudo().create(pick_vals_td)
                        if picking_id_st:
                            picking_id_st.action_confirm()


                if rec.request_action  == 'purchase_order':
                    partner = self.env['res.partner'].search([('name', 'ilike', 'internal purchase request')])[0] if self.env['res.partner'].search([('name', 'ilike', 'internal purchase request')]) else False
                    if partner not in po_dict:
                        po_vals = {
                            'partner_id':partner.id,
                            'currency_id':rec.env.user.company_id.currency_id.id,
                            'date_order':fields.Date.today(),
                            'company_id':rec.env.user.company_id.id,
                            'custom_request_id':rec.id,
                            'branch_outlet_id': rec.branch_outlet_id.id,
                            'picking_type_id': rec.branch_outlet_id.warehouse_id.in_type_id.id,
                            'origin': rec.name,
                            'user_id': self.env.user.id,
                        }
                        purchase_order = purchase_obj.sudo().create(po_vals)
                        po_dict.update({partner:purchase_order})
                        po_line_vals =  {
                                 'product_id': line.product_id.id,
                                 'name':line.product_id.name,
                                 'product_qty': line.qty,
                                 'product_uom': line.uom_id.id,
                                 'date_planned': fields.Date.today(),
                                 'price_unit': line.product_id.lst_price,
                                 'order_id': purchase_order.id,
                        }
                        purchase_line_obj.sudo().create(po_line_vals)
                        rec.write({
                            'state': 'received'
                        })
                    else:
                        purchase_order = po_dict.get(partner)
                        po_line_vals =  {
                             'product_id': line.product_id.id,
                             'name':line.product_id.name,
                             'product_qty': line.qty,
                             'product_uom': line.uom_id.id,
                             'date_planned': fields.Date.today(),
                             'price_unit': line.product_id.lst_price,
                             'order_id': purchase_order.id,
                        }
                        purchase_line_obj.sudo().create(po_line_vals)


    def _prepare_pick_dest_vals_from_src(self, pick=False, stock_id=False):
        transit_location = self.env['stock.location'].search([
            ('usage', '=', 'transit'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal'),
                                                                       ('warehouse_id', '=',
                                                                        self.branch_outlet_id.warehouse_id.id)],limit=1)

        move_lines = []
        for line in pick.move_lines:
            if line.quantity_done > 0:
                pick_vals = {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'location_id': transit_location.id,
                    'location_dest_id': self.branch_outlet_id.warehouse_id.lot_stock_id.id,
                    'name': line.name,
                    'picking_id': stock_id.id,
                    'branch_outlet_id': self.branch_outlet_id.id,
                    'company_id': self.company_id.id,
                    'value': line.product_id.standard_price * line.product_uom_qty,
                    'picking_type_id': picking_type.id
                }
                move_lines.append((0,0, pick_vals))
        return move_lines

    def action_show_po(self):
        for rec in self:
            purchase_action = self.env.ref('purchase.purchase_rfq')
            purchase_action = purchase_action.read()[0]
            purchase_action['domain'] = str([('custom_request_id', '=', rec.id)])
        return purchase_action

    def action_show_mo(self):
        for rec in self:
            mo_action = self.env.ref('mrp.mrp_production_action')
            mo_action = mo_action.read()[0]
            mo_action['domain'] = str([('custom_request_id', '=', rec.id)])
        return mo_action

    def action_reject(self):
        for rec in self:
            rec.write({'state': 'reject'})

    @api.onchange('user_id')
    def user_id_change(self):
        if self.user_id:
            self.branch_outlet_id = self.user_id.branch_outlet_id.id

    @api.onchange('user_id')
    def _onchange_user_id(self):
        self.branch_outlet_id = False

    @api.model
    def create(self, vals):
        """ sequence is created for material request."""
        name = self.env['ir.sequence'].next_by_code('material.request.seq')
        vals.update({
            'name': name
        })
        res = super(MaterialRequest, self).create(vals)
        return res

    def show_picking(self):
        """ Redirects to the stock picking view."""
        for rec in self:
            res = self.env.ref('stock.action_picking_tree_all')
            res = res.read()[0]
            res['domain'] = str([('request_id', '=', rec.id)])
        return res
        return

    def action_cancel(self):
        for rec in self:
            if rec.request_action == 'purchase_order':
                pos = self.env['purchase.order'].search([('custom_request_id', '=', rec.id)])
                for po in pos:
                    for pick in po.picking_ids:
                        pick.action_cancel()
                        pick.action_set_draft()
                        pick.unlink()
                    po.button_cancel()
                    po.unlink()
            if rec.request_action == 'internal_picking':
                pickings = self.env['stock.picking'].search([('request_id', '=', rec.id)])
                for picking in pickings:
                    picking.action_cancel()
                    picking.action_set_draft()
                    picking.unlink()
            rec.write({
                'state': 'reject'
            })


    def unlink(self):
        for record in self:
            # if record.state == 'received' or record.state == 'approve':
            #     raise UserError(_('You cannot delete a request which is confirmed !'))
            # else:
                pickings = self.env['stock.picking'].search([('request_id', '=', record.id)])
                if pickings:
                    for picking in pickings:
                        picking.action_cancel()
        return super(MaterialRequest, self).unlink()
