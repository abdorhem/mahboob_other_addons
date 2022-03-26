
from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError


class MoCreateWizard(models.TransientModel):
    _name = 'create.mo.wiz'
    _description = "Create MO Wizard"

    def no_mo(self):
        rec = self.env['material.request'].browse(self._context.get('active_id'))
        if not rec.source_outlet_id.warehouse_id:
            raise UserError(_('Please Select Warehouse for Source Outlet.'))
        elif not rec.branch_outlet_id.warehouse_id:
            raise UserError(_('Please Select Warehouse for Destination Outlet'))
        else:
            rec.write({'state': 'confirm'})
            rec.action_approve()

    def create_mo(self):
        mo_rec = self.env['material.request'].browse(self._context.get('active_id'))
        bom_pro_lst = [req for req in mo_rec.request_line_ids if req.product_id.variant_bom_ids if req.product_id.variant_bom_ids[0].type == 'normal']
        oth_pro_lst = [req for req in mo_rec.request_line_ids if req.product_id.variant_bom_ids if req.product_id.variant_bom_ids[0].type != 'normal']
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> bom_pro_lst', bom_pro_lst)
        for rec in bom_pro_lst:
            flag = True
            if rec and rec.product_id and rec.product_id.product_tmpl_id.id and rec.qty > 0:
                bom_obj = self.env['mrp.bom']
                bom_id = bom_obj._bom_find(rec.product_id.product_tmpl_id, rec.product_id)
                # rec.product_id.product_tmpl_id._compute_cost_from_bom()
                if bom_id:
                    if bom_id.type == 'normal':
                        mrp_production = self.env['mrp.production']
                        default_dict = mrp_production.default_get(['priority', 'date_planned_start', 'product_uom_id',
                                                                   'product_uom_qty', 'user_id', 'company_id',
                                                                   'name', 'date_planned', 'message_follower_ids'])
                        default_dict.update({
                            'date_planned_start': rec.request_id.request_date,
                            'product_tmpl_id': rec.product_id.product_tmpl_id.id,
                            'product_id': rec.product_id.id,
                            'custom_request_id': rec.request_id.id,
                            'bom_id': bom_id.id or False,
                            'product_qty': rec.qty,
                            'product_uom_id': rec.product_id.uom_id.id,
                            'origin': rec.request_id.name,
                            'product_uom_qty': rec.qty,
                            'company_id': rec.request_id.company_id.id,
                            'location_src_id': rec.request_id.source_outlet_id.warehouse_id.lot_stock_id.id,
                            'location_dest_id': rec.request_id.source_outlet_id.warehouse_id.lot_stock_id.id,
                            'branch_outlet_id': rec.request_id.source_outlet_id.id or False,
                            'picking_type_id': rec.request_id.source_outlet_id.warehouse_id.manu_type_id.id,
                        })
                       
                        mo_id = mrp_production.create(default_dict)
                        mo_id._onchange_product_qty()
                        mo_id._onchange_bom_id()
                        mo_id.product_qty = rec.qty
                        mo_id._onchange_date_planned_start()
                        mo_id.action_assign()
                        mo_id._onchange_move_raw()
                        mo_id._onchange_move_finished()
                        mo_id.action_confirm()
                        mo_id.action_assign()
                        immediate_production_id = self.env['mrp.immediate.production']
                        res = immediate_production_id.with_context({
                            'default_mo_ids' : [(4, mo_id.id)]
                        }).default_get(['immediate_production_line_ids'])
                        rec = immediate_production_id.create(res)
                        rec.process()
                        mo_id.button_mark_done()
        if not mo_rec.source_outlet_id.warehouse_id:
            raise UserError(_('Please Select Warehouse for Source Outlet.'))
        elif not mo_rec.branch_outlet_id.warehouse_id:
            raise UserError(_('Please Select Warehouse for Destination Outlet'))
        else:
            mo_rec.write({'state': 'confirm'})
            mo_rec.action_approve()
