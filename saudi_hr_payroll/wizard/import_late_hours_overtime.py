
from dateutil.relativedelta import relativedelta
import calendar
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import Warning
from odoo import models, fields, exceptions, api, _
import io
import datetime
import base64
import tempfile
import binascii
import logging
_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')
# for xls
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')


class HrPayrollOvertime(models.TransientModel):
    _name = "import.latehour.overtime"
    _description = "Import Latehour Overtime"

    excel_file = fields.Binary('Excel File')
    excel_filename = fields.Char('Excel File Name')

    def import_xls(self):
        try:
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.excel_file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            product_obj = self.env['product.product']

        except Exception:
            raise exceptions.Warning(_("Invalid file!"))



        flag = 0
        generate_hour = self.env['generate.latehour']
        generate_hour_late_history = self.env['employee.late.history']
        counter_product = 0.0
        date_start= False
        date_end= False
        for row_no in range(0,2):
            val = {}
            row_values = sheet.row_values(row_no)
            if row_no == 0:
                date_start = datetime.datetime(*xlrd.xldate_as_tuple(row_values[1], workbook.datemode))
            if row_no ==1:
                date_end = datetime.datetime(*xlrd.xldate_as_tuple(row_values[1], workbook.datemode))
        for row_no in range(3,sheet.nrows):
            row_values = sheet.row_values(row_no)

            employee = self.env['hr.employee'].sudo().search([('barcode','=',int(row_values[0]))],limit=1)
            if employee:
                generate_hour_late_history.sudo().create(
                    {
                        'employee_id': employee.id,
                        'date_start': date_start,
                        'date_end': date_end,
                        'badge_id': int(row_values[0]),
                        'late_hour': float(row_values[1]),
                        'overtime_hour': float(row_values[2])
                    }
                )

                flag = 1
            else:
                raise Warning(_('Employee Not Found  "%s"') % int(row_values[0]))
        if flag == 1:
            return {
                'name': _('Success'),
                'view_mode': 'form',
                'res_model': 'generate.latehour',
                'view_id': self.env.ref('saudi_hr_payroll.success_import_wizard_hr').id,
                'type': 'ir.actions.act_window',
                'target': 'new'
            }
        else:
            return True


class gen_inv_2(models.Model):
    _name = "generate.latehour"
    _description = "Generate Latehour"

    hour_counter_main = fields.Integer("Counter")

