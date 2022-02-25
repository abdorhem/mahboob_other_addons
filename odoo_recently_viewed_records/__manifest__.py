# -*- coding: utf-8 -*-
#################################################################################
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
#################################################################################
{
  "name"                 :  "Odoo Recently Viewed Records",
  "summary"              :  """Odoo Recently Viewed Records allows Odoo User to track your latest ten visited records.""",
  "category"             :  "Extra Tools",
  "version"              :  "1.2.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Recently-Viewed-Records.html",
  "description"          :  """Records
Tracking Records in Odoo
Track Records
Odoo Recently Viewed Records
Recently Viewed Records in Odoo
Recently Viewed Records
Latest Viewed Records
View latest records
Track recent activities 
Recent Activities
Track activities
Latest activities
Tracking Recently Accessed Records
Recently Accessed Records
Tracking Recently Accessed Activities""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=odoo_recently_viewed_records",
  "depends"              :  ['mail'],
  "data"                 :  [
                             'views/template.xml',
                             'security/ir.model.access.csv',
                            ],
  "qweb"                 :  ['static/src/xml/recently_record_widget.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  35,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}
