# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import io
import lxml.html
import datetime
from odoo.http import request

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

from dateutil.relativedelta import relativedelta

from odoo.tools.float_utils import float_round

from odoo import api, fields, models, _
from odoo.tools import date_utils


class InventoryMovementReport(models.AbstractModel):
    _name = 'scrap.report'
    _description = 'Scrap Report'

    def get_reports_buttons(self):
        return [{'name': _('Print Preview'), 'action': 'print_pdf'}, {'name': _('Export (XLSX)'), 'action': 'print_xlsx'}]

    def _get_report_name(self):
        return _('Scrap Report')

    def get_report_filename(self, options):
        """The name that will be used for the file when downloading pdf,xlsx,..."""
        return self._get_report_name().lower().replace(' ', '_')

    def _get_report_super_columns(self, options):
        columns = [
            {'string': _('Reference')},
            {'string': _('Expected Date')},
            {'string': _('Outlet')},
            {'string': _('Branch')},
            {'string': _('Product')},
            {'string': _('Scrap Qty')},
            {'string': _('UOM')},
            {'string': _('Status')},

        ]
        return {'columns': columns, 'x_offset': 0, 'merge': 0}

    @api.model
    def _get_report_lines(self, options):
        lines = []
        results = self._get_inventory_movement_data(options)
        for values in results:
            lines.append({
                'name': '',
                'columns': [{'name': v} for v in [
                        values['ref'],
                        values['expected_date'] or '',
                        values['outlet'] or '',
                        values['branch'] or '',
                        values['product_name'] or '',
                        values['qty'],
                        values['uom'],
                        values['status'],
                    ]
                ],
            })
        total_vals = self._get_header_values(results)
        lines.append({
            'name': '',
            'level': 2,
            'columns': [{'name': ''}] * 2 + [{'name': v} for v in [
                    total_vals['total_qty'],
                                   ]
            ],
        })
        return lines

    def get_report_pdf(self, options, minimal_layout=True):
        base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        rcontext = {
            'mode': 'print',
            'base_url': base_url,
            'company': self.env.user.company_id,
        }

        body = self.env['ir.ui.view'].render_template(
            "scrap_report.print_template",
            values=dict(rcontext),
        )

        body_html = self.with_context(print_mode=True).get_html(options)['html']
        body = body.replace(b'<body class="o_stock_reports_body_print">', b'<body class="o_stock_reports_body_print">' + body_html)
        if minimal_layout:
            header = ''
            footer = self.env['ir.actions.report'].render_template("web.internal_layout", values=rcontext)
            spec_paperformat_args = {'data-report-margin-top': 10, 'data-report-header-spacing': 10}
            footer = self.env['ir.actions.report'].render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=footer))
        else:
            rcontext.update({
                    'css': '',
                    'o': self.env.user,
                    'res_company': self.env.user.company_id,
                })
            header = self.env['ir.actions.report'].render_template("web.external_layout", values=rcontext)
            header = header.decode('utf-8') # Ensure that headers and footer are correctly encoded
            spec_paperformat_args = {}
            # parse header as new header contains header, body and footer
            try:
                root = lxml.html.fromstring(header)
                match_klass = "//div[contains(concat(' ', normalize-space(@class), ' '), ' {} ')]"

                for node in root.xpath(match_klass.format('header')):
                    headers = lxml.html.tostring(node)
                    headers = self.env['ir.actions.report'].render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=headers))

                for node in root.xpath(match_klass.format('footer')):
                    footer = lxml.html.tostring(node)
                    footer = self.env['ir.actions.report'].render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=footer))

            except lxml.etree.XMLSyntaxError:
                headers = header
                footer = ''
            header = headers

        return self.env['ir.actions.report']._run_wkhtmltopdf(
            [body],
            header=header, footer=footer,
            landscape=True,
            specific_paperformat_args=spec_paperformat_args
        )

    def print_pdf(self, options):
        return {
            'type': 'ir_actions_stock_report_download',
            'data': {
                'model': self.env.context.get('model') or self._name,
                'options': json.dumps(options),
                'report_format': 'pdf',
            }
        }

    def get_xlsx(self, options, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self._get_report_name()[:31])

        default_col1_style = workbook.add_format({'font_name': 'Verdana', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        default_style = workbook.add_format({'font_name': 'Verdana', 'font_size': 12, 'font_color': '#666666'})
        title_style = workbook.add_format({'font_name': 'Verdana', 'bold': True, 'bottom': 2})
        super_col_style = workbook.add_format({'font_name': 'Verdana', 'bold': True, 'align': 'center'})
        level_0_style = workbook.add_format({'font_name': 'Verdana', 'bold': True, 'font_size': 13, 'bottom': 6, 'font_color': '#666666'})
        level_1_style = workbook.add_format({'font_name': 'Verdana', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666'})
        level_2_col1_style = workbook.add_format({'font_name': 'Verdana', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_2_col1_total_style = workbook.add_format({'font_name': 'Verdana', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_2_style = workbook.add_format({'font_name': 'Verdana', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_3_col1_style = workbook.add_format({'font_name': 'Verdana', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        level_3_col1_total_style = workbook.add_format({'font_name': 'Verdana', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_3_style = workbook.add_format({'font_name': 'Verdana', 'font_size': 12, 'font_color': '#666666'})

        #Set the first two column width
        sheet.set_column(0, 0, 20)
        sheet.set_column(0, 1, 30)

        super_columns = self._get_report_super_columns(options)
        y_offset = 1

        sheet.write(y_offset, 0, '', title_style)

        x = super_columns.get('x_offset', 0)
        for super_col in super_columns.get('columns', []):
            cell_content = super_col.get('string', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
            x_merge = super_columns.get('merge')
            if x_merge and x_merge > 1:
                sheet.merge_range(0, x, 0, x + (x_merge - 1), cell_content, super_col_style)
                x += x_merge
            else:
                sheet.write(0, x, cell_content, super_col_style)
                x += 1
        lines = self._get_report_lines(options)
        #write all data rows
        for y in range(0, len(lines)):
            level = lines[y].get('level')
            if lines[y].get('caret_options'):
                style = level_3_style
                col1_style = level_3_col1_style
            elif level == 0:
                y_offset += 1
                style = level_0_style
                col1_style = style
            elif level == 1:
                style = level_1_style
                col1_style = style
            elif level == 2:
                style = level_2_style
                col1_style = 'total' in lines[y].get('class', '').split(' ') and level_2_col1_total_style or level_2_col1_style
            elif level == 3:
                style = level_3_style
                col1_style = 'total' in lines[y].get('class', '').split(' ') and level_3_col1_total_style or level_3_col1_style
            else:
                style = default_style
                col1_style = default_col1_style

            for x in range(0, len(lines[y]['columns'])):
                sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, lines[y]['columns'][x].get('name', ''), style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def print_xlsx(self, options):
        return {
            'type': 'ir_actions_stock_report_download',
            'data': {
                'model': self.env.context.get('model') or self._name,
                'options': json.dumps(options),
                'report_format': 'xlsx',
            }
        }

    def _get_scrap_data(self, domain):
        MO = self.env['stock.move']
        MO.check_access_rights('read')
        query = MO._where_calc(domain)
        MO._apply_ir_rules(query, 'read')
        from_clause, where_clause, params = query.get_sql()

        query_str = """
                        SELECT stock_move.picking_id,stock_move.product_id,stock_move.product_qty, stock_move.name, stock_move.location_dest_id,stock_move.date
                        FROM {}
                        WHERE {}
                        GROUP BY stock_move.product_id
                    """.format(from_clause, where_clause)
        self.env.cr.execute(query_str, params)
        picking, product_qtys, product_mo, product_values, product_move_ids = {}, {}, {}, {}, {}
        for mo_id, product_id, qty, name, location, date in self.env.cr.fetchall():
            product_qtys[product_id] = qty
        return product_qtys

    def _report_display_fields(self):
        return [
                ('qty', 'qty'),
            ]

    def _get_header_values(self, values):
        res = dict()
        for key, field in self._report_display_fields():
            res['total_' + field] = sum([value.get(field, 0.0) for value in values])
        return res

    def _build_production_domain(self, report_options):
        domain = []
        if report_options.get('products', []):
            domain += [('product_id', 'in', [int(product_id) for product_id in report_options.get('products')])]
        if report_options.get('categories', []):
            domain += [('product_id.categ_id', 'child_of', [int(categ_id) for categ_id in report_options.get('categories')])]
        if report_options.get('outlets', []):
            domain += [('branch_outlet_id', 'in', [int(branch_outlet_id) for branch_outlet_id in report_options.get('outlets')])]
        if report_options.get('branch', []):
            domain += [('company_branch_id', 'in', [int(company_branch_id) for company_branch_id in report_options.get('branch')])]
        if report_options.get('region', []):
            domain += [('branch_outlet_id.region_id', 'in', [int(region_id) for region_id in report_options.get('region')])]
        return domain

    def _get_date_range_dates(self, search_filters, display_for_qweb=False):
        options = search_filters
        date_from = None
        date_to = datetime.date.today()
        options_filter = 'today'
        if options.get('date') and options['date'].get('filter'):
            options_filter = options['date']['filter']
            if options_filter == 'custom':
                if options.get('date') and options['date'].get('date_from') is None:
                    date_from = None
                    date_to = fields.Date.from_string(options['date']['date'])
                else:
                    date_from = fields.Date.from_string(options['date']['date_from'])
                    date_to = fields.Date.from_string(options['date']['date_to'])
            elif options_filter == 'today':
                date_from = datetime.date.today()
                date_to = date_from + relativedelta(days=1)
                # date_to = datetime.date.today()
            elif options_filter == 'week':
                date_from = date_utils.start_of(date_to, 'week')
                date_to = date_utils.end_of(date_to, 'week')
            elif options_filter == 'month':
                date_from, date_to = date_utils.get_month(date_to)
        if display_for_qweb:
            date_from = fields.Date.from_string(date_from)
            date_to = fields.Date.from_string(date_to)
        return {
            'date_from': date_from,
            'date_to': date_to,
        }


    def _get_inventory_movement_data(self, search_filters, pagerState={}):
        Move = self.env['stock.scrap']
        domain = []
        domain_to_move = []

        dates = self._get_date_range_dates(search_filters)
        date_from = datetime.datetime.combine(dates['date_from'], datetime.datetime.min.time()) - relativedelta(hours=3)
        date_to = datetime.datetime.combine(dates['date_to'], datetime.datetime.max.time()) - relativedelta(hours=3)
        if dates.get('date_from'):
            domain_to_move += [('date_done', '>=', date_from)]
        if dates.get('date_to'):
            domain_to_move += [('date_done', '<=', date_to)]
        domain_to_move += domain
        domain_to_move += self._build_production_domain(search_filters)
        scraps = Move.sudo().search(domain_to_move,
                                    limit=pagerState.get('limit', 0),
                                    offset=pagerState.get('offset', 0))
        domain_to_move = [('date_done', '=', False)]
        if dates.get('date_from'):
            domain_to_move += [('create_date', '>=', date_from)]
        if dates.get('date_to'):
            domain_to_move += [('create_date', '<=', date_to)]
        other_scraps = Move.sudo().search(domain_to_move,
                                    limit=pagerState.get('limit', 0),
                                    offset=pagerState.get('offset', 0))
        scraps = scraps + other_scraps
        res = dict()
        for scrap in scraps:
                sp_id = scrap.id
                res[sp_id] = {}
                res[sp_id]['id'] = scrap.id
                res[sp_id]['ref'] = scrap.name
                res[sp_id]['expected_date'] = (scrap.date_done + relativedelta(hours=3)).strftime('%d-%m-%Y %H:%M:%S') if scrap.date_done else False
                res[sp_id]['outlet'] = scrap.branch_outlet_id.name if scrap.branch_outlet_id else False
                res[sp_id]['branch'] = scrap.company_branch_id.name if scrap.company_branch_id else False
                res[sp_id]['product_id'] = scrap.product_id.id
                res[sp_id]['product_name'] = scrap.product_id.with_context(
                    report_scrap=True
                ).name_get()[0][1]
                res[sp_id]['qty'] = scrap.scrap_qty
                res[sp_id]['uom'] = scrap.product_uom_id.name
                res[sp_id]['status'] = scrap.state
        return res.values()

    def _built_search_options(self):
        # company_ids = get_user_companies(self._cr, self.env.user.id)
        companies = self.env['res.company'].browse(self.env.company.id)
        options = {
            'date': {'filter': 'today', 'date_from': False, 'date_to': datetime.date.today()},
            'multi_company': [],
            'm2m_filters': [
                {'field': 'products', 'label': _('Products'), 'model': 'product.product', 'domain': [('type', '=', "product")]},
                {'field': 'categories', 'label': _('Categories'), 'model': 'product.category', 'domain': []},
                {'field': 'outlets', 'label': _('Outlets'), 'model': 'res.branch.outlet', 'domain': []},
                {'field': 'branch', 'label': _('Branch'), 'model': 'res.company.branch', 'domain': []},
                {'field': 'region', 'label': _('Region'), 'model': 'res.country.state', 'domain': []},


            ]
        }
        if self.env.user.has_group('base.group_multi_company'):
            options.update({'multi_company': [{'id': c.id, 'name': c.name, 'selected': True if c.id == self.env.user.company_id.id else False} for c in companies]})
        return options

    def _parse_search_filters_JSON(self, search_filters):
        dates = self._get_date_range_dates(search_filters, display_for_qweb=True)
        search_filters['date']['date_from'] = dates.get('date_from')
        search_filters['date']['date_to'] = dates.get('date_to')
        return search_filters

    @api.model
    def get_html(self, search_filters={}, pagerState={}):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        format_precision = lambda value: '%.{precision}f'.format(precision=precision) % value
        domain = [
        ]
        domain_to_move = []
        dates = self._get_date_range_dates(search_filters)
        date_from = datetime.datetime.combine(dates['date_from'], datetime.datetime.min.time()) - relativedelta(hours=3)
        date_to = datetime.datetime.combine(dates['date_to'], datetime.datetime.max.time()) - relativedelta(hours=3)
        if dates.get('date_from'):
            domain_date_from = [('date_done', '>=', date_from)]
            domain += domain_date_from
            domain_to_move += domain_date_from
        if dates.get('date_to'):
            domain_date_to = [('date_done', '<=', date_to)]
            domain += domain_date_to
            domain_to_move += domain_date_to
        domain_to_move += domain
        domain_to_move += self._build_production_domain(search_filters)
        records_count = self.env['stock.scrap'].sudo().search_count(domain_to_move)
        limit_per_page = min(int(self.env['ir.config_parameter'].sudo().get_param(
                'scrap_report.scrap_rec_limit')) or 80, pagerState.get('limit', 80))
        pagerState.update({'limit': limit_per_page})

        lines = self._get_inventory_movement_data(search_filters, pagerState)
        res_company = self.env.user.company_id
        if search_filters.get('company_id', False):
            res_company = self.env['res.company'].browse(search_filters['company_id'])

        html = self.env.ref('scrap_report.report_scrap')._render({
            'report_name': self._get_report_name(),
            'res_company': res_company,
            'options': self._parse_search_filters_JSON(search_filters),
            'lines': lines,
            'header_vals': self._get_header_values(lines),
            'currency_id': self.env.user.company_id.currency_id,
            'print_mode': self._context.get('print_mode', False),
            'format_precision': format_precision
        })

        replace_class = {b'table-responsive': b'', b'<a': b'<span', b'</a>': b'</span>'}
        if self._context.get('print_mode', False):
            for k,v in replace_class.items():
                html = html.replace(k, v)

        return {
            'html': html,
            'buttons': self.get_reports_buttons(),
            'records_count': records_count,
            'limit_per_page': limit_per_page,
            'pagerState': pagerState,
            'search_options': self._built_search_options(),
            'search_filters': search_filters,
        }
