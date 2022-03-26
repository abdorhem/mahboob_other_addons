# -*- coding: utf-8 -*-

from itertools import product
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import json
import datetime
import time
import tempfile
import base64
import pytz
import io
import xlsxwriter
from odoo.tools.misc import get_lang
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.exceptions import UserError
from odoo.tools import date_utils


class ProductCardReport(models.TransientModel):
    _name = "product.card.report"
    _description = "Product Card Report"

    product_ids = fields.Many2many('product.product', string='Product')
    date_from = fields.Date('From', required=True)
    date_to = fields.Date('TO', required=True)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse')
    branch_id = fields.Many2one('res.branch.outlet', string='Branch')


    def print_report(self):
        location_ids = self.location_ids
        product_ids = self.product_ids

        if not location_ids:
                location_ids = self.env['stock.location'].search([])
        if not product_ids:
            product_ids = self.env['product.product'].search([])

        data = {'form': {
            'product_ids': product_ids.ids,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'location_ids': location_ids.ids,
        }}
        return self.env.ref('product_card_report.product_card_report_action').report_action(self, data=data)

    def print_as_tree(self):
        date_from = self.date_from
        date_to = self.date_to
        product_ids = self.product_ids.ids
        location_ids = self.location_ids.ids

        if not location_ids:
                location_ids = self.env['stock.location'].search([]).ids

        if not product_ids:
            product_ids = self.env['product.product'].search([]).ids

        cxt = dict(self.env.context or {})
        cxt = {
            'date_from' :date_from,
            'date_to' :date_to,
            'location_ids' :location_ids,
            'product_ids' :product_ids,
            'company_id' :self.env.context['allowed_company_ids'],
        }

       

        report_obj = self.env['report.product.card.tree'].with_context(cxt).action_sql()

        return {
            'name': _('Product Card Report From : %s To :%s') %(date_from,date_to),
            'view_mode': 'tree',
            'view_id': self.env.ref('product_card_report.product_card_view_view_tree').id,
            'res_model': 'report.product.card.tree',
            'type': 'ir.actions.act_window',
            # 'domain': [('product_id', 'in', product_ids), ('date', '>=', date_from),
            #            ('date', '<=', date_to)
            #            ],
        }

    def get_product_move_lines(self,product_id, date_from, date_to,branch_id):

        params = [  
                     date_from, date_to,branch_id,
                     date_from, date_to,branch_id,
                     date_from, date_to,branch_id,tuple(product_id)
        ]

        query = """
         select 

            pt.name as product_name,
           
            coalesce((select 
            sum (pol.qty)
            from pos_order_line pol
            left join pos_order po on(pol.order_id = po.id)
            left join stock_picking pik on (po.id = pik.pos_order_id)
            left join stock_move sm on (sm.picking_id = pik.id and sm.product_id = p.id)
            where pol.product_id = p.id and date_order >= %s  and date_order <= %s  and po.branch_outlet_id = %s
            ),0) as qty,
            
            coalesce((select 
            sum (pol.price_unit * pol.qty)
            from pos_order_line pol
            left join pos_order po on(pol.order_id = po.id)
            left join stock_picking pik on (po.id = pik.pos_order_id)
            left join stock_move sm on (sm.picking_id = pik.id and sm.product_id =p.id)
            where pol.product_id = p.id and date_order >= %s  and date_order <= %s and po.branch_outlet_id = %s
            ),0) as price,

           
            coalesce((select 
            sum (abs(sm.value / sm.product_uom_qty))
            from pos_order_line pol
            left join pos_order po on(pol.order_id = po.id)
            left join stock_picking pik on (po.id = pik.pos_order_id)
            left join stock_move sm on (sm.picking_id = pik.id and sm.product_id =p.id)
            where pol.product_id = p.id and date_order >= %s  and date_order <= %s and po.branch_outlet_id = %s
            ) ,0) as unit_cost


            from product_product as p
            left join product_template pt on(p.product_tmpl_id = pt.id)
            where p.id in %s


                        """

        self.env.cr.execute(query, tuple(params))
        print(query)
        res = self.env.cr.dictfetchall()
        return res

    def print_xls_report(self):

        branch_id = self.branch_id
        product_ids = self.product_ids


        if not product_ids:
            product_ids = self.env['product.product'].search([('type','=','consu')])
        data = {}
        data['form'] = ({
            'product_ids': product_ids.ids,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'branch_id': branch_id,
        })
        if not data.get('form'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))

        date_from = data['form'].get('date_from')
        date_to = data['form'].get('date_to')
        product_ids = data['form']['product_ids']
        branch_id = data['form']['branch_id']

        temp_location = tempfile.mkstemp()[1]
        workbook = xlsxwriter.Workbook(temp_location + '.xlsx')
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px'})

        format1 = workbook.add_format(
            {'font_size': 11, 'align': 'center', 'bold': True, 'bg_color': '#D3D3D3'})
        format11 = workbook.add_format(
            {'font_size': 11, 'align': 'center', 'bold': True, 'bg_color': '#D3D3D3'})
        format4 = workbook.add_format({'font_size': 22})
        format2 = workbook.add_format(
            {'font_size': 9, 'align': 'left', 'bold': True, })
        format22 = workbook.add_format(
            {'font_size': 9, 'align': 'center', 'bold': True, })
        format3 = workbook.add_format({'font_size': 10})
        format5 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format7 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format7.set_align('center')

        sheet.set_column(0, 0, 60)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 20)
        sheet.set_column(11, 11, 20)
        sheet.set_column(12, 12, 20)
        sheet.set_column(13, 13, 20)
        sheet.set_column(14, 14, 20)
        sheet.set_column(15, 15, 20)

        sheet.merge_range('A2:F3', 'Outlet Sales', head)
        sheet.write('A6', 'From:', format22)
        sheet.write('B6', data["form"]
                    ["date_from"].strftime('%Y/%d/%m'), format22)
        sheet.write('A7', 'To:', format22)
        sheet.write('B7', data["form"]
                    ["date_to"].strftime('%Y/%d/%m'), format22)

        sheet.write(9, 0, 'Outlet', format11)  # 0
        sheet.write(9, 1, 'Quantity', format11)  # 1
        sheet.write(9, 2, 'Total Sales', format11)  # 1
        sheet.write(9, 3, 'Total Cost', format11)  # 2
        sheet.write(9, 4, 'Item Margin', format11)  # 2
        sheet.write(9, 5, 'Total Margin', format11)  # 2
 

        i = 11
        result = self.get_product_move_lines(product_ids, date_from, date_to,branch_id.id)            
        for res in result:
            if  res['qty'] ==0 :
                result.remove(res)
        sheet.merge_range(i,2,i,3,branch_id.name, format22)
        i = i + 2
        for res in result:
            sheet.write(i, 0, res['product_name'], format22)
            sheet.write(i, 1, res['qty'], format22)
            sheet.write(i, 2, res["price"], format22)
            sheet.write(i, 3, res["unit_cost"], format22)
            if res["price"] and ["unit_cost"] :
                sheet.write(i, 4,(res["price"]- res["unit_cost"])/res['qty'], format22)
                sheet.write(i, 5,(res["price"]- res["unit_cost"]), format22)
            sheet.set_row(i, 20)
            i = i + 1
        i = i + 1
        workbook.close()
        name = 'Outlet Sales Report.xlsx'
        data = base64.encodestring(open(temp_location + '.xlsx', 'rb').read())
        report_id = self.env['stock.history.pos'].create({'file': data,
                                                      'name': name})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Outlet Sales Report',
            'res_model': 'stock.history.pos',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': report_id.id,
            'target': 'new',
        }


class StockHistory(models.TransientModel):
    _name = "stock.history.pos"
    _description = ""

    file = fields.Binary(string="File")
    name = fields.Char(string="Name")
