from odoo import api, fields, models


class DepartmentScore(models.Model):
    _name = "ecosphere.department.score"
    _description = "Department ESG Score History"
    _inherit = ["mail.thread"]
    _order = "period desc, department_id"

    department_id = fields.Many2one("hr.department", required=True, index=True)
    period = fields.Char(required=True, help="YYYY-MM or other reporting period")
    environmental_score = fields.Float()
    social_score = fields.Float()
    governance_score = fields.Float()
    total_score = fields.Float()
    calculation_timestamp = fields.Datetime(default=fields.Datetime.now, required=True)
    calculation_details = fields.Text()

    _sql_constraints = [
        ("department_period_unique", "unique(department_id, period)", "A score already exists for this department and period."),
    ]

    @api.model
    def cron_calculate_scores(self):
        period = fields.Date.context_today(self).strftime("%Y-%m")
        for department in self.env["hr.department"].search([("esg_active", "=", True)]):
            self.calculate_department_score(department, period)
        self.env["ecosphere.action.recommendation"].generate_recommendations()

    @api.model
    def calculate_department_score(self, department, period=None):
        period = period or fields.Date.context_today(self).strftime("%Y-%m")
        environmental, env_detail = self._environmental_score(department)
        social, social_detail = self._social_score(department)
        governance, gov_detail = self._governance_score(department)
        params = self.env["ir.config_parameter"].sudo()
        env_w = float(params.get_param("ecosphere_esg.environmental_weight", 40.0)) / 100.0
        social_w = float(params.get_param("ecosphere_esg.social_weight", 30.0)) / 100.0
        gov_w = float(params.get_param("ecosphere_esg.governance_weight", 30.0)) / 100.0
        total = environmental * env_w + social * social_w + governance * gov_w
        details = "\n".join([env_detail, social_detail, gov_detail])
        vals = {
            "environmental_score": environmental,
            "social_score": social,
            "governance_score": governance,
            "total_score": total,
            "calculation_timestamp": fields.Datetime.now(),
            "calculation_details": details,
        }
        score = self.search([("department_id", "=", department.id), ("period", "=", period)], limit=1)
        if score:
            score.write(vals)
        else:
            vals.update({"department_id": department.id, "period": period})
            score = self.create(vals)
        department.write({
            "environmental_score": environmental,
            "social_score": social,
            "governance_score": governance,
            "total_esg_score": total,
            "score_calculation_date": fields.Datetime.now(),
        })
        return score

    def _safe_rate(self, numerator, denominator):
        return 100.0 if not denominator else max(0.0, min(100.0, (numerator / denominator) * 100.0))

    def _environmental_score(self, department):
        Carbon = self.env["ecosphere.carbon.transaction"]
        Goal = self.env["ecosphere.environmental.goal"]
        total = Carbon.search_count([("department_id", "=", department.id)])
        verified = Carbon.search_count([("department_id", "=", department.id), ("verification_status", "=", "verified")])
        goals = Goal.search([("department_id", "=", department.id)])
        goal_score = sum(goals.mapped("progress_percentage")) / len(goals) if goals else 100.0
        coverage = self._safe_rate(verified, total)
        score = (goal_score * 0.6) + (coverage * 0.4)
        return score, "Environmental: goal achievement %.2f, verified coverage %.2f" % (goal_score, coverage)

    def _social_score(self, department):
        employees = self.env["hr.employee"].search([("department_id", "=", department.id)])
        employee_count = len(employees)
        csr = self.env["ecosphere.csr.participation"].search_count([
            ("department_id", "=", department.id),
            ("approval_status", "=", "approved"),
        ])
        challenge = self.env["ecosphere.challenge.participation"].search_count([
            ("department_id", "=", department.id),
            ("approval_state", "=", "approved"),
        ])
        csr_rate = self._safe_rate(csr, employee_count)
        challenge_rate = self._safe_rate(challenge, employee_count)
        engagement = min(100.0, (csr_rate + challenge_rate) / 2.0)
        score = (csr_rate * 0.35) + (challenge_rate * 0.35) + (engagement * 0.30)
        return score, "Social: CSR %.2f, challenge %.2f, engagement %.2f" % (csr_rate, challenge_rate, engagement)

    def _governance_score(self, department):
        employees = self.env["hr.employee"].search([("department_id", "=", department.id)])
        employee_ids = employees.ids
        Ack = self.env["ecosphere.policy.acknowledgement"]
        Issue = self.env["ecosphere.compliance.issue"]
        total_ack = Ack.search_count([("employee_id", "in", employee_ids)])
        done_ack = Ack.search_count([("employee_id", "in", employee_ids), ("status", "=", "acknowledged")])
        total_issues = Issue.search_count([("department_id", "=", department.id)])
        closed_issues = Issue.search_count([("department_id", "=", department.id), ("status", "in", ["verified", "closed"])])
        on_time = Issue.search_count([
            ("department_id", "=", department.id),
            ("status", "in", ["verified", "closed"]),
            ("is_overdue", "=", False),
        ])
        ack_rate = self._safe_rate(done_ack, total_ack)
        closure = self._safe_rate(closed_issues, total_issues)
        timely = self._safe_rate(on_time, closed_issues)
        score = (ack_rate * 0.4) + (closure * 0.35) + (timely * 0.25)
        return score, "Governance: policy %.2f, closure %.2f, on-time %.2f" % (ack_rate, closure, timely)
