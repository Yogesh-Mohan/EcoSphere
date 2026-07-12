from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class PointsTransaction(models.Model):
    _name = "ecosphere.points.transaction"
    _description = "EcoSphere Points Ledger"
    _inherit = ["mail.thread"]
    _order = "date desc, id desc"

    name = fields.Char(default="/", readonly=True)
    employee_id = fields.Many2one("hr.employee", required=True, index=True)
    department_id = fields.Many2one(related="employee_id.department_id", store=True)
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    points = fields.Float(required=True, tracking=True)
    reason = fields.Char(required=True)
    source_model = fields.Char(index=True)
    source_record_id = fields.Integer(index=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    state = fields.Selection([("draft", "Draft"), ("posted", "Posted"), ("cancelled", "Cancelled")], default="posted")

    _sql_constraints = [
        (
            "source_points_unique",
            "unique(employee_id, source_model, source_record_id, reason)",
            "Points were already posted for this employee and source.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = sequence.next_by_code("ecosphere.points.transaction") or "/"
        records = super().create(vals_list)
        records._auto_award_badges()
        return records

    def _auto_award_badges(self):
        enabled = self.env["ir.config_parameter"].sudo().get_param("ecosphere_esg.badge_auto_award", "True") not in ("False", "0", "")
        if enabled:
            self.env["ecosphere.employee.badge"].auto_award_for_employees(self.mapped("employee_id"))


class EmployeeBadge(models.Model):
    _name = "ecosphere.employee.badge"
    _description = "Employee Badge"
    _order = "awarded_date desc"

    employee_id = fields.Many2one("hr.employee", required=True, ondelete="cascade")
    badge_id = fields.Many2one("ecosphere.badge", required=True)
    awarded_date = fields.Datetime(default=fields.Datetime.now, required=True)
    source_note = fields.Char()

    _sql_constraints = [
        ("employee_badge_unique", "unique(employee_id, badge_id)", "This badge was already awarded to the employee."),
    ]

    @api.model
    def auto_award_for_employees(self, employees):
        badges = self.env["ecosphere.badge"].search([("active", "=", True)])
        for employee in employees:
            metrics = self._employee_metrics(employee)
            for badge in badges:
                if badge._compare(metrics.get(badge.metric, 0.0)):
                    self.create_if_missing(employee, badge, "Auto-awarded from structured badge rule.")

    @api.model
    def create_if_missing(self, employee, badge, note=None):
        existing = self.search([("employee_id", "=", employee.id), ("badge_id", "=", badge.id)], limit=1)
        if existing:
            return existing
        record = self.create({"employee_id": employee.id, "badge_id": badge.id, "source_note": note})
        employee.message_post(body="Badge unlocked: %s" % badge.name)
        return record

    @api.model
    def _employee_metrics(self, employee):
        Ledger = self.env["ecosphere.points.transaction"]
        Challenge = self.env["ecosphere.challenge.participation"]
        CSR = self.env["ecosphere.csr.participation"]
        Ack = self.env["ecosphere.policy.acknowledgement"]
        rows = Ledger.read_group(
            [("employee_id", "=", employee.id), ("state", "=", "posted")],
            ["points:sum"],
            ["employee_id"],
        )
        xp = rows[0]["points"] if rows else 0.0
        return {
            "xp": xp,
            "completed_challenges": Challenge.search_count([
                ("employee_id", "=", employee.id),
                ("approval_state", "=", "approved"),
            ]),
            "csr_participation": CSR.search_count([
                ("employee_id", "=", employee.id),
                ("approval_status", "=", "approved"),
            ]),
            "policy_completion": Ack.search_count([
                ("employee_id", "=", employee.id),
                ("status", "=", "acknowledged"),
            ]),
        }


class RewardRedemption(models.Model):
    _name = "ecosphere.reward.redemption"
    _description = "Reward Redemption"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "request_date desc"

    name = fields.Char(default="/", readonly=True)
    employee_id = fields.Many2one("hr.employee", required=True, tracking=True)
    reward_id = fields.Many2one("ecosphere.reward", required=True, tracking=True)
    points_required = fields.Float(related="reward_id.points_required", store=True)
    request_date = fields.Datetime(default=fields.Datetime.now, required=True)
    approved_by_id = fields.Many2one("res.users", readonly=True)
    state = fields.Selection(
        [
            ("requested", "Requested"),
            ("approved", "Approved"),
            ("fulfilled", "Fulfilled"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
        ],
        default="requested",
        tracking=True,
    )
    points_transaction_id = fields.Many2one("ecosphere.points.transaction", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = sequence.next_by_code("ecosphere.reward.redemption") or "/"
        return super().create(vals_list)

    def action_approve(self):
        for redemption in self:
            if redemption.state != "requested":
                continue
            if redemption.employee_id.ecosphere_points_balance < redemption.reward_id.points_required:
                raise UserError("Insufficient points for this reward.")
            if redemption.reward_id.available_stock <= 0:
                raise UserError("Reward stock is not available.")
            redemption.reward_id.available_stock -= 1
            tx = self.env["ecosphere.points.transaction"].create({
                "employee_id": redemption.employee_id.id,
                "points": -redemption.reward_id.points_required,
                "reason": "Reward redemption: %s" % redemption.reward_id.name,
                "source_model": redemption._name,
                "source_record_id": redemption.id,
            })
            redemption.write({
                "state": "approved",
                "approved_by_id": self.env.user.id,
                "points_transaction_id": tx.id,
            })
            redemption.employee_id.message_post(body="Reward redemption approved: %s" % redemption.reward_id.name)

    def action_fulfill(self):
        self.write({"state": "fulfilled"})

    def action_reject(self):
        self.write({"state": "rejected"})

    def action_cancel(self):
        for redemption in self:
            if redemption.state == "approved":
                redemption.reward_id.available_stock += 1
                self.env["ecosphere.points.transaction"].create({
                    "employee_id": redemption.employee_id.id,
                    "points": redemption.reward_id.points_required,
                    "reason": "Reward cancellation restore: %s" % redemption.reward_id.name,
                    "source_model": redemption._name,
                    "source_record_id": redemption.id,
                })
            redemption.state = "cancelled"

    @api.constrains("reward_id")
    def _check_stock_not_negative(self):
        for redemption in self:
            if redemption.reward_id.available_stock < 0:
                raise ValidationError("Reward stock cannot be negative.")
