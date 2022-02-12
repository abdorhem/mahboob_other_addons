# -*- coding: utf-8 -*-

from locale import currency
from odoo import models, fields, api


class contract(models.Model):
    _name = 'contract.license'
    _description = 'contract.license'

    name = fields.Char('Name')
    number = fields.Integer('Number')
    date = fields.Date('Date')
    renew_date = fields.Date('Renew Date')
    end_date = fields.Date('End Date')
    image = fields.Binary('Image')
    penalty_ids = fields.One2many('contract.license.line', 'licence_id')


class ContractLine(models.Model):
    _name = 'contract.license.line'
    _description = 'license line'

    licence_id = fields.Many2one('contract.license', string='licence')
    
    name = fields.Char('Name')
    amount = fields.Integer('Amount')
    image = fields.Binary('Image')



#  ---------------    Contracts    -----------------------------
class ContractContract(models.Model):
    _name = 'contract.contract'
    _description = 'contract.contract'

    name = fields.Char('Name')
    owner = fields.Char('Owner')
    date = fields.Date('Date')
    image = fields.Binary('Image')
    
    water = fields.Char('Water Meter')
    pay_w = fields.Char('Pay/month')
    
    elec = fields.Char('Elec. Meter')
    pay_e = fields.Char('Pay/month')
    
    renew = fields.Selection(
        string='Renew',
        selection=[('month', '6 Month'),
        ('year', 'Year')
        ]
    )
    

#  ---------------    C.R    -----------------------------
class ContractContract(models.Model):
    _name = 'company.reg'
    _description = 'Company Regestry'

    name = fields.Char('Name')
    number = fields.Char('Number')
    location = fields.Char('Location')
    id_id = fields.Char('ID')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    image = fields.Binary('Image')
    
    renew = fields.Selection(
        string='Renew',
        selection=[('month', '6 Month'),
        ('year', 'Year'),
        ('2year', '2 Years'),
        ('3year', '3 Years'),
        ('4year', '4 Years'),
        ]
    )
    

#  ---------------    Car    -----------------------------
class ContractContract(models.Model):
    _name = 'car.car'
    _description = 'Cars'

    model = fields.Char('Model')
    number = fields.Char('Number')
    type = fields.Char('Type')
    driver_id = fields.Many2one('hr.employee', string='Driver')
    condition = fields.Char('Condition')
    city = fields.Char('City')

    date_id = fields.Date('Date of license')
    date_id_end = fields.Date('End of license')
    fhs = fields.Date('Fahs')
    end_fhs = fields.Date('End of Fahs')
    drivr_con = fields.Date('Driver Confirm')
    end_driver_con = fields.Date('End of Confirmation')
    note = fields.Text('Note')
    image = fields.Binary('Image')



    sim = fields.Char('Sim')
    sensors = fields.Selection(
        string='Sensors',
        selection=[('yes', 'Yes'),
        ('no', 'No'),  
        ]
    )
    gps = fields.Selection(
        string='GPS',
        selection=[('yes', 'Yes'),
        ('no', 'No'),  
        ]
    )

    oil_change = fields.One2many('oil.line', 'car_id', string='Oil Change')
    penalty = fields.One2many('car.penalty', 'car_id', string='Penalties')
    fule = fields.One2many('car.fule', 'car_id', string='Fuel')


    class CarOil(models.Model):
        _name = 'oil.line'
        _description = 'license line'

        car_id = fields.Many2one('car.car', string='')
        
        odo_befor = fields.Char('Odo before')
        odo_after = fields.Char('Odo After')
        oil_change = fields.Date('Change Date')

    class CarPenalty(models.Model):
        _name = 'car.penalty'
        _description = ''

        car_id = fields.Many2one('car.car', string='')
        
        name = fields.Many2one('hr.employee', string='Driver')
        type = fields.Char('Type')
        amount = fields.Char('Amount')
        date = fields.Date('Date')
        image = fields.Binary('Image')

    class Fule(models.Model):
        _name = 'car.fule'
        _description = ''

        car_id = fields.Many2one('car.car', string='')
        
        date = fields.Date('Date')
        liter = fields.Char('Leters')
        amount = fields.Float('amount')
        type = fields.Selection([
            ('d', 'Desiel'),
            ('p', 'Petrol'),
        ], string='Fule Type')
   

#  ---------------    buildings    -----------------------------
class Buildings(models.Model):
    _name = 'buildings.buildings'

    name = fields.Char('Name')
    location = fields.Char('Owner')
    city = fields.Char('City')
    number = fields.Char('Number')
    amount = fields.Float('Amount')
    image = fields.Binary('Image')
  
    date_start = fields.Date('Start Date')
    date_to = fields.Date('End Date')
    
    
    type = fields.Selection(
        string='Type',
        selection=[('month', '6 Month'),
        ('year', 'Year')
        ]
    )


    def _crone (self) :
        objs = self.env['buildings.buildings'].search([])
        for obj in objs :
            s=obj.date_start
            t=obj.date_to
            if (t-s).days == 27 :
                print("############################################### date_start",obj)
                print("############################################### date_start",s)
                print("############################################### date_to",t)
                print("############################################### sub",(t-s).days)



#  ---------------    medical cer.    -----------------------------
class Buildings(models.Model):
    _name = 'med.certificate'

    name_id = fields.Many2one('hr.employee', string='Name')
    idn = fields.Char('ID')
    outlet_id = fields.Many2one('res.branch.outlet', string='Outlet')
    date = fields.Date('End Date')
    image = fields.Binary('Image')
    
    type = fields.Selection(
        string='Type',
        selection=[('random', 'Random'),
        ('usual', 'Usualy')
        ]
    )


  