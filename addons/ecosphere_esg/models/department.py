from odoo import api, fields, models


class HrDepartment(models.Model):
    _inherit = "hr.department"

    esg_manager_id = fields.Many2one("res.users", string="ESG Manager")
    parent_esg_department_id = fields.Many2one("hr.department", string="Parent ESG Department")
    environmental_score = fields.Float(readonly=True)
    social_score = fields.Float(readonly=True)
    governance_score = fields.Float(readonly=True)
    total_esg_score = fields.Float(readonly=True)
    score_calculation_date = fields.Datetime(readonly=True)
    esg_active = fields.Boolean(string="ESG Active", default=True)
    carbon_transaction_count = fields.Integer(compute="_compute_esg_counts")
    compliance_issue_count = fields.Integer(compute="_compute_esg_counts")

    def _compute_esg_counts(self):
        Carbon = self.env["ecosphere.carbon.transaction"]
        Issue = self.env["ecosphere.compliance.issue"]
        for department in self:
            department.carbon_transaction_count = Carbon.search_count([("department_id", "=", department.id)])
            department.compliance_issue_count = Issue.search_count([("department_id", "=", department.id)])

    def action_view_carbon_transactions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Carbon Transactions",
            "res_model": "ecosphere.carbon.transaction",
            "view_mode": "list,form,pivot,graph",
            "domain": [("department_id", "=", self.id)],
            "context": {"default_department_id": self.id},
        }

    def action_view_compliance_issues(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Compliance Issues",
            "res_model": "ecosphere.compliance.issue",
            "view_mode": "list,form,kanban",
            "domain": [("department_id", "=", self.id)],
            "context": {"default_department_id": self.id},
        }


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    ecosphere_points_balance = fields.Float(compute="_compute_ecosphere_points_balance")
    ecosphere_badge_count = fields.Integer(compute="_compute_ecosphere_counts")
    ecosphere_policy_pending_count = fields.Integer(compute="_compute_ecosphere_counts")

    def _compute_ecosphere_points_balance(self):
        Ledger = self.env["ecosphere.points.transaction"]
        for employee in self:
            rows = Ledger.read_group(
                [("employee_id", "=", employee.id), ("state", "=", "posted")],
                ["points:sum"],
                ["employee_id"],
            )
            employee.ecosphere_points_balance = rows[0]["points"] if rows else 0.0

    def _compute_ecosphere_counts(self):
        Badge = self.env["ecosphere.employee.badge"]
        Ack = self.env["ecosphere.policy.acknowledgement"]
        for employee in self:
            employee.ecosphere_badge_count = Badge.search_count([("employee_id", "=", employee.id)])
            employee.ecosphere_policy_pending_count = Ack.search_count([
                ("employee_id", "=", employee.id),
                ("status", "!=", "acknowledged"),
            ])
