# -*- coding: utf-8 -*-

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"


    esg_public_recognition_opt_in = fields.Boolean(
        string="Show in ESG Recognition",
        default=True,
        help="Allow this employee to appear in ESG leaderboards and recognition cards when permitted by company policy.",
    )
    esg_department_manager_for_ids = fields.One2many(
        comodel_name="hr.department",
        inverse_name="esg_manager_id",
        string="ESG Managed Departments",
        readonly=True,
    )
    esg_total_xp = fields.Float(string="ESG XP", compute="_compute_esg_balances", digits=(16, 2))
    esg_total_points = fields.Float(string="ESG Points", compute="_compute_esg_balances", digits=(16, 2))

    def _compute_esg_balances(self):
        totals = {employee.id: {"xp_amount": 0.0, "points_amount": 0.0} for employee in self}
        if self.ids:
            groups = self.env["esg.xp.ledger"].read_group(
                [("employee_id", "in", self.ids)],
                ["employee_id", "xp_amount:sum", "points_amount:sum"],
                ["employee_id"],
            )
            for group in groups:
                employee_id = group["employee_id"][0]
                totals[employee_id] = {
                    "xp_amount": group.get("xp_amount", 0.0),
                    "points_amount": group.get("points_amount", 0.0),
                }
        for employee in self:
            employee.esg_total_xp = totals[employee.id]["xp_amount"]
            employee.esg_total_points = totals[employee.id]["points_amount"]
