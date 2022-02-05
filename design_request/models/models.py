# -*- coding: utf-8 -*-

from odoo import models, fields, api


class design_request(models.Model):
    _name = 'design_request.design_request'
    _inherit = ['mail.thread']

    _description = 'Design Request'


    name = fields.Char('Name')
    designer_id = fields.Many2one('hr.employee', string='Designer')
    requester = fields.Many2one('res.partner', string='Requester')
    department = fields.Many2one('hr.department', string='Department')
    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
    )
  
    image = fields.Binary('Image')
    
    image1 = fields.Binary('Image')
    txt1 = fields.Text('Text')
    comment1 = fields.Text('Comment')
    image2 = fields.Binary('Image')
    txt2 = fields.Text('Text')
    comment2 = fields.Text('Comment')
    image3 = fields.Binary('Image')
    txt3 = fields.Text('Text')
    comment3 = fields.Text('Comment')



    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approve'),
        ('ceo', 'Marketing Approve'),
        ('phase1', 'Phase 1'),
        ('approve1', 'Waiting Approve'),
        ('phase2', 'Phase 2'),
        ('approve2', 'Waiting Approve'),
        ('phase3', 'Phase 3'),
        ('approve3', 'Waiting Approve'),
        ('back', 'Back To Designer'),
        ('cancel', 'Cancelled'),
        ('done', 'Done'),
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
   
    def approve(self):
        for record in self:
            record.state = 'ceo'

    def ceo(self):
        for record in self:
            record.state = 'phase1'

    def phase1(self):
        for record in self:
            record.state = 'approve1'
    
    def approve1(self):
        for record in self:
            record.state = 'done'

    def phase2(self):
        for record in self:
            record.state = 'approve2'
    
    def approve2(self):
        for record in self:
            record.state = 'done'

    def phase3(self):
        for record in self:
            record.state = 'approve3'

    def approve3(self):
        for record in self:
            record.state = 'done'

    def done(self):
        for record in self:
            record.state = 'done'

    def cancel(self):
        for record in self:
            record.state = 'cancel'

    def back(self):
            if self.state == 'approve1' :
                self.state = 'phase2' 
            else :
                self.state = 'phase3' 


class OfferRequest(models.Model):
    _name = 'offer.request'
    _description = 'Offer Request'

    name = fields.Char('Name')
    
    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
    )
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    description = fields.Text('Description')
    image = fields.Binary('Image')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approve'),
        ('op_approve', 'Operation Approve'),
        ('account_approve', 'Accounting Approval'),
        ('ceo', 'CEO Approval'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
   
    def approve(self):
        for record in self:
            record.state = 'approve'

    def op_approve(self):
        for record in self:
            record.state = 'op_approve'

    def account_approve(self):
        for record in self:
            record.state = 'account_approve'
    
    def ceo(self):
        for record in self:
            record.state = 'ceo'

    def cancel(self):
        for record in self:
            record.state = 'cancel'
