# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def name_get(self):
        result = super(ProductProduct, self).name_get()
        if self._context.get('report_scrap', False):
            result1 = list()
            for product in self:
                for res in result:
                    result1.append((product.id, res[1].replace('[%s]'
                                                               % product.default_code, '').strip()))
            return result1
        return result
