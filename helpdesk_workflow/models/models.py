# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError



class WrkeFlow(models.Model):
    _inherit = 'helpdesk.ticket'


    def action_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self.env['ir.model.data'].xmlid_to_res_id('helpdesk_workflow.overdue_ticket_request_email_template', raise_if_not_found=False)
        template = self.env['mail.template'].browse(template_id)

        ctx = {
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def to_overdue (self) :
        obl =self.env['helpdesk.ticket'].search([('is_ticket_closed','!=',True),('assign_date','!=',False)]) 
        stage =self.env['helpdesk.stage'].search([('is_overdue','=',True)]) 
        for rec in obl :
            days = stage.days
            if rec.team_id in stage.team_ids :
                if (datetime.now() - rec.assign_date).days > days :
                    rec.stage_id = stage

class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'



  
    is_overdue = fields.Boolean('Is Overdue')
    
    days = fields.Integer(
        string='Overdue days',
    )
     

    @api.onchange('is_overdue')
    def _onchange_(self):
        obj =self.env['helpdesk.stage'].search([]) 
        for rec in obj :
            if rec.is_overdue :
                  raise ValidationError(_(
                    "Overdue stage must be only one !"))
