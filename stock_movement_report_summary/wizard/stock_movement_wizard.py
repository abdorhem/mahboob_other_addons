# -*- coding: utf-8 -*-

import base64
import tempfile
from datetime import datetime

import pytz
import xlsxwriter
from dateutil.relativedelta import relativedelta
from pytz import timezone, UTC

from odoo import fields, models


class StockHistorySummary(models.TransientModel):
    _name = "stock.history.summary"
    _description = "Stock History Summary"

    file = fields.Binary(string="File")
    name = fields.Char(string="Name")


class StockMovementReportSummaryWizard(models.TransientModel):
    _name = "stock.movement.report.summary.wizard"
    _description = "Stock Movement Report Summary Wizard"

    start_date = fields.Date(
        string='Start Date', required=True
    )

    end_date = fields.Date(
        string='End Date', required=True
    )

    location_id = fields.Many2many(
        'stock.location', string='Location',
        required=True, domain=[('usage', '=', 'internal')]
    )

    product_ids = fields.Many2many(
        'product.product', string='Products',
    )

    def get_date(self, report_date):
        # Method to convert date according to the user's timezone
        tz = 'Asia/Riyadh'
        return timezone(tz).localize(fields.Datetime.from_string(
            report_date)).astimezone(UTC)

    def get_converted_date(self, report_date):
        tz = 'Asia/Riyadh'
        return timezone('UTC').localize(fields.Datetime.from_string(
            report_date)).astimezone(pytz.timezone(tz))

    def _get_stock_move_data_op(self, domain):
        StockMove = self.env['stock.move']
        StockMove.check_access_rights('read')
        query = StockMove._where_calc(domain)
        StockMove._apply_ir_rules(query, 'read')
        from_clause, where_clause, params = query.get_sql()

        query_str = """ SELECT stock_move.product_id, SUM(COALESCE(stock_move.product_qty, 0.0)), 
                        SUM(COALESCE(stock_move.{}, 0.0)), ARRAY_AGG(stock_move.id)
                        FROM {}
                        WHERE {}
                        GROUP BY stock_move.product_id
                    """.format("value", from_clause, where_clause)
        self.env.cr.execute(query_str, params)
        product_qtys_op, product_values_op, product_move_ids = {}, {}, {}
        for product_id, qty, value, move_ids in self.env.cr.fetchall():
            product_qtys_op[product_id] = qty
            product_values_op[product_id] = value
            # product_move_ids[product_id] = move_ids
        return product_qtys_op, product_values_op

    def generate_report(self):
        temp_location = tempfile.mkstemp()[1]
        workbook = xlsxwriter.Workbook(temp_location + '.xlsx')
        worksheet = workbook.add_worksheet()
        worksheet.set_column("A:B", 12)
        worksheet.set_column("C:C", 24)
        worksheet.set_column("D:D", 10)
        worksheet.set_column("E:E", 24)
        worksheet.set_column("F:J", 14)
        center = workbook.add_format({'align': 'center'})
        row = 1
        heading = [
            ['Date', 'Code', 'ProductName', 'UOM',
             'Opening Qty', 'Incoming Qty', 'Outgoing Qty',
             'Balance', 'Balance Value'
             ]
        ]
        worksheet.write_row("A2:M2", heading[0])
        name = "Stock Movement Report Summary.xlsx"
        st_dt = self.start_date.strftime('%d/%m/%Y')
        end_dt = self.end_date.strftime('%d/%m/%Y')
        to_date = self.end_date.strftime('%Y-%m-%d')
        worksheet.merge_range(0, 0, 0, 10, 'Location: ' + self.location_id.name + ' / Date Range: ' + st_dt +
                              ' To ' + end_dt, center)
        product_ids = self.product_ids if self.product_ids else self.env['product.product'].sudo().search([])

        start_date = datetime.combine(self.start_date, datetime.min.time()) - relativedelta(hours=3)
        end_date = datetime.combine(self.end_date, datetime.max.time()) - relativedelta(hours=3)
        StockMove = self.env['stock.move']
        domain_move_in = [
            ('state', '=', 'done'),
        ]
        domain_move_out = [
            ('state', '=', 'done'),
        ]

        domain_move_in = [('product_id', 'in', product_ids.ids)] + \
                         domain_move_in
        domain_move_out = [('product_id', 'in', product_ids.ids)] + \
                          domain_move_out
        if self.location_id.ids:
            domain_move_in += [('location_dest_id', 'in', self.location_id.ids)]
            domain_move_out += [('location_id', 'in', self.location_id.ids)]

        domain_move_in_past = domain_move_in
        domain_move_out_past = domain_move_out
        domain_move_in_op = []
        domain_move_out_op = []
        domain_move_in_op += domain_move_in
        domain_move_out_op += domain_move_out

        if self.start_date:
            domain_move_in_op += [('date', '<', start_date)]
            domain_move_out_op += [('date', '<', start_date)]
            domain_date_from = [('date', '>=', start_date)]
            domain_move_in += domain_date_from
            domain_move_out += domain_date_from
        if self.end_date:
            domain_date_to = [('date', '<=', end_date)]
            domain_move_in += domain_date_to
            domain_move_out += domain_date_to
            domain_move_in_past += [('date', '<=', end_date)]
            domain_move_out_past += [('date', '<=', end_date)]

        product_qty_op_in, product_values_op_in = self._get_stock_move_data_op(domain_move_in_op)
        product_qty_op_out, product_values_op_out = self._get_stock_move_data_op(domain_move_out_op)
        total_value = 0.0
        for product in product_ids:
            for loc in self.location_id:
                start_date = datetime.combine(self.start_date, datetime.min.time()) - relativedelta(hours=3)
                end_date = datetime.combine(self.end_date, datetime.max.time()) - relativedelta(hours=3)

                sql_query = """SELECT p.default_code, p.id as product_id,
                                   pt.name as product, categ.name as category_name,sm.date as date,sm.picking_id,
                                   uom.name as uom_name, spt.code,sm.location_dest_id, sm.location_id, 
                                   sm.product_uom_qty,sm.id as id,sm.group_id as group_id
                                   from stock_move as sm 
                                   LEFT JOIN product_product as p ON p.id = sm.product_id
                                   LEFT JOIN uom_uom as uom ON uom.id = sm.product_uom
                                   LEFT JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id
                                   LEFT JOIN product_template as pt ON p.product_tmpl_id = pt.id 
                                   LEFT JOIN product_category as categ ON categ.id = pt.categ_id 
                                   LEFT JOIN stock_picking as sp ON sp.id = sm.picking_id 
                                   where (sm.location_id=%s or sm.location_dest_id=%s) and 
                                   sm.date >= %s and sm.date <= %s and sm.state='done' and sm.product_id=%s 
                                   group by pt.name, p.default_code, uom.name, pt.categ_id, categ.name,
                                    sm.date,spt.code,
                                   sm.location_dest_id, sm.location_id, sm.product_uom_qty, sm.id,
                                   p.id 
                                   order by date asc"""
                param = (loc.id, loc.id, start_date, end_date, product.id)
                self.env.cr.execute(sql_query, param)
                query_rec = self.env.cr.dictfetchall()
                colm = 0
                if query_rec:
                    opening_dict = product.with_context(to_date=query_rec[0].get('date').strftime('%Y-%m-%d 00:00:00'),
                                                        location=loc.id)._product_available()
                    op_stock = 0.0
                    op_val = 0.0
                    op_val1 = 0.0
                    if opening_dict.get(product.id):
                        if opening_dict.get(product.id).get('qty_available') != 0.0:
                            # op_stock = opening_dict.get(product.id).get('qty_available')
                            op_stock = product_qty_op_in.get(product.id, 0.0) - product_qty_op_out.get(product.id, 0.0)
                            op_val = opening_dict.get(product.id).get('qty_available') * product.standard_price
                            op_val1 = opening_dict.get(product.id).get('qty_available') * product.standard_price
                for sql_dict in query_rec:

                    if self.env['stock.move'].browse(sql_dict.get('id')):
                        converted_date = self.get_converted_date(str(sql_dict.get('date')))
                        pur_qty = 0.0
                        if sql_dict.get('code') == 'incoming':
                            pur_qty = sql_dict.get('product_uom_qty')
                        tran_in_qty = 0.0
                        tran_avg_cost = 0
                        if sql_dict.get('code') == 'internal':
                            if sql_dict.get('location_dest_id') == loc.id:
                                tran_in_qty = sql_dict.get('product_uom_qty')

                                self.env.cr.execute(
                                    """select sum(price_unit*qty_received)/sum(CASE COALESCE(qty_received, 0) 
                                    WHEN 0 THEN 1.0 ELSE qty_received END) from purchase_order_line 
                                    where product_id = %s and (date_planned::date) >= %s
                                     and (date_planned::date) <= %s and  location_dest_id = %s 
                                     and order_id in (select po.id from purchase_order po where po.state ='done')""",
                                    (product.id, self.start_date, self.end_date, sql_dict.get('location_id')))
                                tran_avg_cost_result = self.env.cr.fetchall()
                                if tran_avg_cost_result[0][0] != None:
                                    tran_avg_cost = tran_avg_cost_result[0][0]

                        tran_out_qty = 0.0
                        if sql_dict.get('code') == 'internal':
                            if sql_dict.get('location_id') == loc.id:
                                tran_out_qty = sql_dict.get('product_uom_qty')
                        man_qty_in = 0.0
                        man_qty_out = 0.0
                        if sql_dict.get('code') == 'mrp_operation':
                            if sql_dict.get('location_dest_id') == loc.id:
                                man_qty_in = sql_dict.get('product_uom_qty')
                            if sql_dict.get('location_id') == loc.id:
                                man_qty_out = sql_dict.get('product_uom_qty')
                        sale_qty = 0.0
                        pos_qty = 0.0
                        if sql_dict.get('code') == 'outgoing':
                            if sql_dict.get('picking_id'):
                                if self.env['stock.picking'].browse(sql_dict.get('picking_id')).pos_order_id:
                                    pos_qty = sql_dict.get('product_uom_qty')
                                else:
                                    sale_qty = sql_dict.get('product_uom_qty')
                            else:
                                sale_qty = sql_dict.get('product_uom_qty')
                        adjust_qty_in = 0.0
                        cons_mo_in = 0.0
                        if sql_dict.get('code') is None:
                            if sql_dict.get('location_dest_id') == loc.id:
                                if not sql_dict.get('picking_id') and sql_dict.get('group_id'):
                                    cons_mo_in = sql_dict.get('product_uom_qty')
                                else:

                                    adjust_qty_in = sql_dict.get('product_uom_qty')
                        adjust_qty_out = 0.0
                        cons_mo_out = 0.0
                        if sql_dict.get('code') is None:
                            if sql_dict.get('location_id') == loc.id:
                                if not sql_dict.get('picking_id') and sql_dict.get('group_id'):
                                    cons_mo_out = sql_dict.get('product_uom_qty')
                                else:
                                    adjust_qty_out = sql_dict.get('product_uom_qty')

                        from_date = str(
                            datetime.combine(sql_dict.get('date'), datetime.min.time()) - relativedelta(hours=3))
                        acc_date = str(
                            datetime.combine(sql_dict.get('date'), datetime.max.time()) - relativedelta(hours=3))
                        if loc:
                            self.env.cr.execute(
                                """select sum(price_unit*qty_received)/sum(CASE COALESCE(qty_received, 0) 
                                WHEN 0 THEN 1.0 ELSE qty_received END) from purchase_order_line 
                                where product_id = %s and date_planned >= %s and date_planned <= %s 
                                and  location_dest_id in %s and order_id in (select po.id 
                                from purchase_order po where po.state ='done')""",
                                (product.id, from_date, acc_date, tuple(loc.ids)))
                        else:
                            self.env.cr.execute(
                                """select sum(price_unit*qty_received)/sum(CASE COALESCE(qty_received, 0)
                                 WHEN 0 THEN 1.0 ELSE qty_received END) from purchase_order_line 
                                 where product_id = %s and date_planned >= %s and date_planned <= %s 
                                 and order_id in (select po.id from purchase_order po where po.state ='done')""",
                                (product.id, start_date, end_date))
                        result = self.env.cr.fetchall()

                        self.env.cr.execute(
                            """select sum(price_unit*qty_received)/sum(CASE COALESCE(qty_received, 0) 
                            WHEN 0 THEN 1.0 ELSE qty_received END) from purchase_order_line
                             where product_id = %s and date_planned <= %s and order_id in (select po.id 
                             from purchase_order po where po.state ='done')""",
                            (product.id, acc_date))

                        result2 = self.env.cr.fetchall()
                        avg_cost = 0.0
                        if result[0][0] != None:
                            avg_cost = result[0][0]
                        elif result2[0][0] != None:
                            avg_cost = result2[0][0]
                        price = avg_cost
                        received_qty = pur_qty
                        # received_val = received_qty * price
                        received_val = self.env['stock.move'].browse(
                            sql_dict.get('id')).purchase_line_id.price_subtotal if self.env['stock.move'].browse(
                            sql_dict.get('id')).purchase_line_id and pur_qty != 0.0 else 0.0
                        received_val1 = sum(self.env['stock.move'].browse(sql_dict.get('id')).account_move_ids.mapped(
                            'amount_untaxed')) if received_qty and self.env['stock.move'].browse(
                            sql_dict.get('id')).account_move_ids else 0.0

                        issue_qty = sale_qty
                        # issue_val = issue_qty * price
                        issue_val = price * issue_qty

                        transfer_in_qty = tran_in_qty
                        transfer_out_qty = tran_out_qty
                        transfer_in_val = tran_avg_cost * transfer_in_qty
                        transfer_out_val = price * transfer_out_qty
                        issue_val1 = sum(self.env['stock.move'].browse(sql_dict.get('id')).account_move_ids.mapped(
                            'amount_untaxed')) if issue_qty and self.env['stock.move'].browse(
                            sql_dict.get('id')).account_move_ids else 0.0
                        consumption_qty = pos_qty
                        # consumption_val = consumption_qty *price
                        consumption_val = price * consumption_qty
                        consumption_val1 = sum(
                            self.env['stock.move'].browse(sql_dict.get('id')).account_move_ids.mapped(
                                'amount_untaxed')) if consumption_qty and self.env['stock.move'].browse(
                            sql_dict.get('id')).account_move_ids else 0.0
                        adst_qty_in = adjust_qty_in + cons_mo_in
                        cons_mo_qty_in = cons_mo_in + man_qty_in
                        cons_mo_qty_out = cons_mo_out + man_qty_out
                        # cons_mo_val_in = cons_mo_qty_in * price
                        cons_mo_val_in = price * cons_mo_qty_in
                        cons_mo_val_in1 = sum(self.env['stock.move'].browse(sql_dict.get('id')).account_move_ids.mapped(
                            'amount_untaxed')) if cons_mo_qty_in and self.env['stock.move'].browse(
                            sql_dict.get('id')).account_move_ids else 0.0
                        # cons_mo_val_out = cons_mo_qty_out * price
                        cons_mo_val_out = price * cons_mo_qty_out
                        cons_mo_val_out1 = sum(
                            self.env['stock.move'].browse(sql_dict.get('id')).account_move_ids.mapped(
                                'amount_untaxed')) if cons_mo_qty_out and self.env['stock.move'].browse(
                            sql_dict.get('id')).account_move_ids else 0.0
                        # adjust_val_in = (adjust_qty_in) * price
                        adjust_val_in = price * adjust_qty_in
                        adjust_val_in1 = sum(self.env['stock.move'].browse(sql_dict.get('id')).account_move_ids.mapped(
                            'amount_untaxed')) if adjust_qty_in and self.env['stock.move'].browse(
                            sql_dict.get('id')).account_move_ids else 0.0
                        # adjust_val_out = (adjust_qty_out) * price
                        adjust_val_out = price * adjust_qty_out
                        adjust_val_out1 = sum(self.env['stock.move'].browse(sql_dict.get('id')).account_move_ids.mapped(
                            'amount_untaxed')) if adjust_qty_out and self.env['stock.move'].browse(
                            sql_dict.get('id')).account_move_ids else 0.0

                        balance = round(
                            op_stock + (received_qty + tran_in_qty) - (issue_qty + tran_out_qty) - consumption_qty - (
                                        adjust_qty_out + cons_mo_qty_out) + (adjust_qty_in + cons_mo_qty_in), 4)
                        balance_val = round(op_val1 + received_val1 - issue_val1 - consumption_val1 - (
                                    adjust_val_out1 + cons_mo_val_out1) + (adjust_val_in1 + cons_mo_val_in1), 4)
                        balance_val1 = round(balance, 4) * avg_cost

                        row += 1
                        worksheet.write(row, colm, acc_date)
                        worksheet.write(row, colm + 1, product.default_code)
                        worksheet.write(row, colm + 2, product.name)
                        worksheet.write(row, colm + 3, product.uom_name)
                        worksheet.write(row, colm + 4, op_stock)
                        total_incoming = received_qty + transfer_in_qty + cons_mo_qty_in + adst_qty_in
                        total_outgoing = issue_qty + transfer_out_qty + consumption_qty + \
                                         cons_mo_qty_out + adjust_qty_out
                        worksheet.write(row, colm + 5, total_incoming if total_incoming != 0 else '')
                        worksheet.write(row, colm + 6, total_outgoing if total_outgoing != 0 else '')
                        worksheet.write(row, colm + 7, round(balance, 4) if balance != 0 else '')
                        worksheet.write(row, colm + 8, round(balance_val1, 4) if balance_val1 != 0 else '')

                        op_stock = round(balance, 4)
                        op_val1 = round(balance_val, 4)
                        total_value += round(balance_val1)

        worksheet.write(row+1, 7, "TOTAL VALUE")
        worksheet.write(row+1, 8, total_value)
        workbook.close()
        data = base64.encodestring(open(temp_location + '.xlsx', 'rb').read())
        report_id = self.env['stock.history'].create({'file': data,
                                                      'name': name})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Movement Report Summary',
            'res_model': 'stock.history',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': report_id.id,
            'target': 'new',
        }
