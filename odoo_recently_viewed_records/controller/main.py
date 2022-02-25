# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
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

import logging
_logger = logging.getLogger(__name__)

from odoo.http import request
from odoo import http, SUPERUSER_ID


class RecentlyViewedRecord(http.Controller):

    @http.route(
        ['/recently/view/records'], type='json', auth='public', csrf=False)
    def recently_view_record(
            self, name=False, url=False, record_id=False, model=False,
            action=False, **post):
        result = {'status': True}
        records = request.env['recently.viewed.record'].search([
            ('record_id', '=', record_id), ('model', '=', model),
            ('user_id', '=', request._uid)], limit=1)
        if not records:
            if action and name and record_id and model:
                action_name = request.env['ir.actions.act_window'].browse(
                    action).name
                request.env['recently.viewed.record'].create({
                    'name': action_name + '/' + name, 'url': url,
                    'record_id': record_id, 'model': model,
                    'user_id': request._uid})
            elif name and record_id and model:
                request.env['recently.viewed.record'].create({
                    'name': '' + '/' + name, 'url': url,
                    'record_id': record_id, 'model': model,
                    'user_id': request._uid})
            else:
                return {}
        else:
            records.write({'url': url, })
            result['status'] = False
        request._cr.commit()
        if result['status']:
            result['records_list'] = self._get_recently_record()
        return result

    @http.route([
        '/get/recently/view/records'], type='json', auth='public', csrf=False)
    def get_recently_view_record(self, **post):
        return self._get_recently_record()

    def _get_recently_record(self):
        records = request.env['recently.viewed.record'].search(
            [('user_id', '=', request._uid)])
        records_list = []
        for record in records:
            record_dict = {'name': record.name, 'id': record.record_id,
                           'model': record.model, 'url': record.url}
            records_list.append(record_dict)
        return records_list
