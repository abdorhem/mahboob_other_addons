from odoo import models, fields, api


class ResBranchOutlet(models.Model):
    _inherit = "res.branch.outlet"
    warehouse_manager_id = fields.Many2one("hr.employee", "Warehouse Manager")
