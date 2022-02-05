# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from datetime import datetime

from odoo import api, fields, models,_
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockScrapGroup(models.Model):
    _name = 'group.stock.scrap'
    _description = "Group Stock Scrap Order"
    _inherit = ['mail.thread']


    def _get_default_scrap_location_id(self):
        return self.env['stock.location'].search([('scrap_location', '=', True), ('company_id', 'in', [self.env.user.company_id.id, False])], limit=1).id

    def _get_default_location_id(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        return None

    name = fields.Char(
        string='Number',
        index=True,
        readonly=1,default=lambda self: _('New')
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('partial', 'Partially Done'),
        ('confirm', 'Confirmed')],
        tracking=True, default='draft'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Requested By',
        default=lambda self: self.env.user and self.env.user.id or False,
        required=True,
        copy=True,
        tracking=True
    )

    scrap_ids = fields.One2many('stock.scrap','group_id', tracking=True)
    date_expected = fields.Datetime('Expected Date', default=fields.Datetime.now,states={'confirm': [('readonly', True)]})
    location_id = fields.Many2one(
        'stock.location', 'Location', domain="[('usage', '=', 'internal')]",
        required=True, states={'confirm': [('readonly', True)]}, default=_get_default_location_id
    , tracking=True)
    scrap_location_id = fields.Many2one(
        'stock.location', 'Scrap Location', default=_get_default_scrap_location_id,
        domain="[('scrap_location', '=', True)]", required=True, states={'confirm': [('readonly', True)]}
    , tracking=True)

    scrap_type_ids = fields.Many2many('stock.scrap.type', string="Scrap type")

    branch_outlet_id = fields.Many2one(
        'res.branch.outlet',
        string="Outlet",states={'confirm': [('readonly', True)]},
        copy=False,
        default=lambda self: self.env.user.branch_outlet_id.id, tracking=True
    )
    company_branch_id = fields.Many2one(
        'res.company.branch', string="Company Branch",states={'confirm': [('readonly', True)]},
        related='branch_outlet_id.company_branch_id', store=True, tracking=True)

    @api.onchange('date_expected')
    def onchange_date_expected(self):
        if self.env.user.has_group('dwf.group_dwf_date_restriction'):
            if self.date_expected:
                if self.date_expected.date() < (datetime.today().date() - relativedelta(days=self.env.user.restricted_dates)):
                    self.date_expected = False
            if self.date_expected:
                if self.date_expected.date() > (datetime.today().date() + relativedelta(days=self.env.user.restricted_dates)):
                    self.date_expected = False

    @api.onchange('branch_outlet_id')
    def _onchange_branch_outlet_id(self):
        if self.branch_outlet_id:
            self.location_id = self.branch_outlet_id.warehouse_id.lot_stock_id.id

    @api.model
    def create(self, vals):
        """ sequence is created for material request."""
        name = self.env['ir.sequence'].next_by_code('group.stock.scrap.seq')
        vals.update({
            'name': name
        })
        message = ''
        outlet_obj = self.env['res.branch.outlet']
        location_obj = self.env['stock.location']
        partner_obj = self.env['res.partner']
        package_obj = self.env['stock.quant.package']
        product_obj = self.env['product.product']
        scrap_obj = self.env['stock.scrap']
        uom_obj = self.env['uom.uom']
        picking_obj = self.env['stock.picking']
        msg_lst = []
        for scrap in vals.get('scrap_ids',[]):
            if scrap[0] == 0:
                message = '<b>' + 'Created' + '</b>' + '<br/> '
                for key, val in scrap[2].items():
                    if key == 'branch_outlet_id':
                        message += _('Outlet' + ' : ' + outlet_obj.browse(
                            val).name) + '<br/>'
                    elif key == 'location_id':
                        if location_obj:
                            message += _('Location' + ' : ' + location_obj.browse(
                                val).name) + '<br/>'
                    elif key == 'scrap_location_id':
                        message += _(
                            'Scrap Location' + ' : ' + location_obj.browse(
                                val).name) + '<br/>'
                    elif key == 'owner_id':
                        message += (_(
                            'Owner' + ' : ' + partner_obj.browse(val).name) + '<br/>') if partner_obj.browse(
                            val) else ''
                    elif key == 'package_id':
                        message += (_(
                            'Package' + ' : ' + package_obj.browse(val).name) + '<br/>') if package_obj.browse(
                            val) else ''
                    elif key == 'product_uom_id':
                        message += _(
                            'UOM' + ' : ' + uom_obj.browse(val).name) + '<br/>'
                    elif key == 'product_id':
                        message += _(
                            'Product' + ' : ' + product_obj.browse(val).name) + '<br/>'
                    elif key == 'picking_id':
                        message += (_(
                            'Picking' + ' : ' + picking_obj.browse(val).name) + '<br/>') if picking_obj.browse(
                            val) else ''
                    elif key == 'scrap_qty':
                        message += _('Quantity' + ' : ' + str(val)) + '<br/>'
                    else:
                        message += _(key + ' : ' + str(val)) + '<br/>'
            msg_lst.append(message)
        res = super(StockScrapGroup, self).create(vals)
        for scrap in res.scrap_ids:
            scrap.origin = res.name
        for msg in msg_lst:
            res.message_post(body=msg)
        return res

    def write(self, vals):
        """ sequence is created for material request."""
        message = ''
        outlet_obj = self.env['res.branch.outlet']
        location_obj = self.env['stock.location']
        partner_obj = self.env['res.partner']
        package_obj = self.env['stock.quant.package']
        product_obj = self.env['product.product']
        scrap_obj = self.env['stock.scrap']
        uom_obj = self.env['uom.uom']
        picking_obj = self.env['stock.picking']
        msg_lst = []
        for scrap in vals.get('scrap_ids',[]):
            if scrap[0] == 0:
                message = '<b>' +'Created'+'</b>' + '<br/> '
                for key, val in scrap[2].items():
                    if key == 'branch_outlet_id':
                        message += _('Outlet' + ' : ' +  outlet_obj.browse(
                            val).name) + '<br/>'
                    elif key == 'location_id':
                        message += _('Location' + ' : ' + location_obj.browse(
                            val).name) + '<br/>'
                    elif key == 'scrap_location_id':
                        message += _(
                            'Scrap Location' + ' : ' + location_obj.browse(
                                val).name) + '<br/>'
                    elif key == 'owner_id':
                        message += (_(
                            'Owner' + ' : ' + partner_obj.browse(val).name) + '<br/>') if partner_obj.browse(val) else ''
                    elif key == 'package_id':
                        message += (_(
                            'Package' + ' : '  + package_obj.browse(val).name) + '<br/>') if package_obj.browse(val) else ''
                    elif key == 'product_uom_id':
                        message += _(
                            'UOM' + ' : ' + uom_obj.browse(val).name) + '<br/>'
                    elif key == 'product_id':
                        message += _(
                            'Product' + ' : ' + product_obj.browse(val).name) + '<br/>'
                    elif key == 'picking_id':
                        message += (_(
                            'Picking' + ' : ' + picking_obj.browse(val).name) + '<br/>') if  picking_obj.browse(val) else ''
                    elif key == 'scrap_qty':
                        message += _('Quantity' + ' : ' + str(val)) + '<br/>'
                    else:
                        message += _(key + ' : ' + str(val)) + '<br/>'
                message += _('User' + ' : ' + self.env.user.name) + '<br/>'
                msg_lst.append(message)
            if scrap[0] == 1:
                rec = scrap_obj.browse(scrap[1])
                message = '<b>' + 'Updated' + '</b>' + ' : ' + rec.product_id.name + '<br/>'
                for key,val in scrap[2].items():
                    if key == 'branch_outlet_id':
                        message += _('Outlet' + ' : ' + rec.branch_outlet_id.name + ' -> ' + outlet_obj.browse(val).name) + '<br/>'
                    elif key == 'location_id':
                        message += _('Location' + ' : ' + rec.location_id.name + ' -> ' + location_obj.browse(val).name) + '<br/>'
                    elif key == 'scrap_location_id':
                        message += _('Scrap Location' + ' : ' + rec.scrap_location_id.name + ' -> ' + location_obj.browse(val).name) + '<br/>'
                    elif key == 'owner_id':
                        message += _('Owner' + ' : ' + rec.owner_id.name + ' -> ' + partner_obj.browse(val).name) + '<br/>'
                    elif key == 'package_id':
                        message += _('Package' + ' : ' + rec.package_id.name + ' -> ' + package_obj.browse(val).name) + '<br/>'
                    elif key == 'product_uom_id':
                        message += _('UOM' + ' : ' + rec.product_uom_id.name + ' -> ' + uom_obj.browse(val).name) + '<br/>'
                    elif key == 'product_id':
                        message += _('Product' + ' : ' + rec.product_id.name + ' -> ' + product_obj.browse(val).name) + '<br/>'
                    elif key == 'picking_id':
                        message += _(
                            'Picking' + ' : ' + picking_obj.browse(val).name) + '<br/>'
                    elif key == 'scrap_qty':
                        message += _('Quantity' + ' : ' + str(rec.scrap_qty) + ' -> ' + str(val)) + '<br/>'
                    else:
                        message += _(key + ' : ' + str(val)) + '<br/>'
                message += _('User' + ' : ' + self.env.user.name) + '<br/>'
                msg_lst.append(message)
            if scrap[0] == 2:
                rec = scrap_obj.browse(scrap[1])
                message = '<b>' + 'Deleted' + '</b>' + ' : ' + rec.product_id.name + '<br/>'
                message += _('User' + ' : ' + self.env.user.name) + '<br/>'
                msg_lst.append(message)
        for msg in msg_lst:
            self.message_post(body=msg)
        res = super(StockScrapGroup, self).write(vals)
        return res

    def action_validate(self):
        if not self.scrap_ids:
            raise UserError(_('Please Enter Scrap Orders'))
        for scrap in self.scrap_ids:
            if scrap.state == 'draft':
                self.ensure_one()
                if scrap.product_id.type != 'product':
                    return scrap.do_scrap()
                precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                available_qty = sum(self.env['stock.quant']._gather(scrap.product_id,
                                                                    scrap.location_id,
                                                                    scrap.lot_id,
                                                                    scrap.package_id,
                                                                    scrap.owner_id,
                                                                    strict=True).mapped('quantity'))
                scrap_qty = scrap.product_uom_id._compute_quantity(scrap.scrap_qty, scrap.product_id.uom_id)
                if float_compare(available_qty, scrap_qty, precision_digits=precision) >= 0:
                    scrap.do_scrap()
                else:
                    insufficient_qty_wizard = self.env['stock.warn.insufficient.qty.scrap'].create({
                        'product_id': scrap.product_id.id,
                        'location_id': scrap.location_id.id,
                        'scrap_id': scrap.id
                    })
                    insufficient_qty_wizard.action_done()
        res = []
        [res.append(x) for x in self.scrap_ids.mapped('state') if x not in res]
        if len(res) > 1:
            self.write({'state': 'partial'})
        if len(res) == 1:
            if 'done' in res:
                self.write({'state': 'confirm'})
        return

class StockScrapInherit(models.Model):
    _inherit = 'stock.scrap'

    group_id = fields.Many2one('group.stock.scrap')


    date_expected = fields.Datetime('Expected Date', related='group_id.date_expected')
    location_id = fields.Many2one(
        'stock.location', 'Location', domain="[('usage', '=', 'internal')]",
        required=True, states={'confirm': [('readonly', True)]}, related='group_id.location_id', store=True)
    scrap_location_id = fields.Many2one(
        'stock.location', 'Scrap Location', related='group_id.scrap_location_id',
        domain="[('scrap_location', '=', True)]", required=True, states={'confirm': [('readonly', True)]}, store=True)
    branch_outlet_id = fields.Many2one(
        'res.branch.outlet',
        string="Outlet",
        copy=False,
        related='group_id.branch_outlet_id', store=True
    )
    company_branch_id = fields.Many2one(
        'res.company.branch', string="Company Branch",
        related='group_id.company_branch_id', store=True)

    @api.model
    def create(self, vals):
        """ sequence is created for material request."""
        name = self.env['ir.sequence'].next_by_code('stock.scrap.seq')
        vals.update({
            'name': name
        })
        res = super(StockScrapInherit, self).create(vals)
        return res

    def do_scrap(self):
        for scrap in self:
            move = self.env['stock.move'].create(scrap._prepare_move_values())
            if move:
                move.resource_operation_type = 'scrap_orders'
                move.resource_ref = scrap.group_id.name
            # master: replace context by cancel_backorder
            force_date = scrap.group_id.date_expected if scrap.group_id else False
            if force_date:
                move.with_context(is_scrap=True, force_period_date=force_date)._action_done()
            else:
                move.with_context(is_scrap=True)._action_done()
            move.date = scrap.group_id.date_expected if scrap.group_id else move.date
            move.date = scrap.group_id.date_expected if scrap.group_id else move.date
            scrap.write({'move_id': move.id, 'state': 'done'})
            scrap.date_done = fields.Datetime.now()
            for line in move.move_line_ids:
                line.date = move.date
                line.resource_operation_type = 'scrap_orders'
                line.resource_ref = scrap.group_id.name
        return True


class StockScrapType(models.Model):
    _name = 'stock.scrap.type'

    name = fields.Char(string='Name')
