# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
##########################################################################

from odoo import models, fields, api, _


class RecentlyViewedRecord(models.Model):

    _name = 'recently.viewed.record'
    _description = "Recently Viewed Records"
    _order = "write_date desc"

    name = fields.Char(string="Name", required=True)
    url = fields.Char(string="URL", required=True)
    user_id = fields.Many2one('res.users', string="User", required=True)
    record_id = fields.Char(string="Record Id", required=True)
    model = fields.Char(string="Model", required=True)


class Users(models.Model):

    _inherit = "res.users"

    recently_viewed_record_ids = fields.One2many(
        'recently.viewed.record', 'user_id', string="Recently Viewed Records")
