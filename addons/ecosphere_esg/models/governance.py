from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PolicyAcknowledgement(models.Model):
    _name = "ecosphere.policy.acknowledgement"
    _description = "Policy Acknowledgement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "assigned_date desc"

    policy_id = fields.Many2one("ecosphere.esg.policy", required=True, ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", required=True)
    policy_version = fields.Char(required=True)
    assigned_date = fields.Date(default=fields.Date.context_today, required=True)
    acknowledgement_date = fields.Datetime()
    status = fields.Selection(
        [("pending", "Pending"), ("acknowledged", "Acknowledged"), ("overdue", "Overdue")],
        default="pending",
        tracking=True,
    )
    employee_confirmation = fields.Boolean()

    _sql_constraints = [
        (
            "policy_employee_version_unique",
            "unique(policy_id, employee_id, policy_version)",
            "This employee already has an acknowledgement for this policy version.",
        ),
    ]

    @api.model
    def create_if_missing(self, policy, employee):
        existing = self.search([
            ("policy_id", "=", policy.id),
            ("employee_id", "=", employee.id),
            ("policy_version", "=", policy.version),
        ], limit=1)
        if existing:
            return existing
        return self.create({
            "policy_id": policy.id,
            "employee_id": employee.id,
            "policy_version": policy.version,
        })

    def action_acknowledge(self):
        self.write({
            "status": "acknowledged",
            "acknowledgement_date": fields.Datetime.now(),
            "employee_confirmation": True,
        })

    @api.model
    def cron_policy_reminders(self):
        today = fields.Date.context_today(self)
        for ack in self.search([("status", "in", ["pending", "overdue"])]):
            if ack.policy_id.review_date and ack.policy_id.review_date < today:
                ack.status = "overdue"
            ack.employee_id.message_post(body="Policy acknowledgement reminder: %s" % ack.policy_id.name)

    @api.model
    def cron_expiring_policy_reminders(self):
        today = fields.Date.context_today(self)
        horizon = fields.Date.add(today, days=30)
        policies = self.env["ecosphere.esg.policy"].search([
            ("state", "=", "published"),
            ("review_date", "!=", False),
            ("review_date", "<=", horizon),
        ])
        for policy in policies:
            policy.message_post(body="Policy review date is approaching.")


class EsgAudit(models.Model):
    _name = "ecosphere.audit"
    _description = "ESG Audit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_date desc"

    name = fields.Char(string="Audit name", required=True, tracking=True)
    audit_type = fields.Selection(
        [("environmental", "Environmental"), ("social", "Social"), ("governance", "Governance"), ("integrated", "Integrated")],
        required=True,
    )
    auditor_id = fields.Many2one("res.users", required=True)
    department_id = fields.Many2one("hr.department")
    scope = fields.Text()
    start_date = fields.Date(required=True)
    end_date = fields.Date()
    description = fields.Html()
    evidence_attachment = fields.Binary()
    evidence_filename = fields.Char()
    result = fields.Text()
    status = fields.Selection(
        [
            ("planned", "Planned"),
            ("in_progress", "In Progress"),
            ("review", "Review"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="planned",
        tracking=True,
    )


class ComplianceIssue(models.Model):
    _name = "ecosphere.compliance.issue"
    _description = "Compliance Issue"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "severity desc, due_date"

    name = fields.Char(string="Issue title", required=True, tracking=True)
    audit_id = fields.Many2one("ecosphere.audit")
    department_id = fields.Many2one("hr.department")
    description = fields.Html()
    severity = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")],
        default="medium",
        tracking=True,
    )
    owner_id = fields.Many2one("res.users", required=True, tracking=True)
    raised_date = fields.Date(default=fields.Date.context_today, required=True)
    due_date = fields.Date(required=True, tracking=True)
    corrective_action = fields.Text()
    evidence = fields.Binary()
    evidence_filename = fields.Char()
    status = fields.Selection(
        [
            ("open", "Open"),
            ("in_progress", "In Progress"),
            ("resolved", "Resolved"),
            ("verified", "Verified"),
            ("closed", "Closed"),
        ],
        default="open",
        tracking=True,
    )
    is_overdue = fields.Boolean(compute="_compute_is_overdue", store=True)
    resolution_date = fields.Datetime()
    verified_by_id = fields.Many2one("res.users", readonly=True)

    @api.depends("due_date", "status")
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for issue in self:
            issue.is_overdue = bool(issue.due_date and issue.due_date < today and issue.status in ["open", "in_progress", "resolved"])

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for issue in records:
            issue.message_post(body="New compliance issue assigned to %s." % issue.owner_id.display_name)
            if issue.severity == "critical":
                issue.activity_schedule(
                    "mail.mail_activity_data_todo",
                    user_id=issue.owner_id.id,
                    summary="Critical compliance issue",
                    note=issue.name,
                )
        return records

    def action_start(self):
        self.write({"status": "in_progress"})

    def action_resolve(self):
        self.write({"status": "resolved", "resolution_date": fields.Datetime.now()})

    def action_verify(self):
        self.write({"status": "verified", "verified_by_id": self.env.user.id})

    def action_close(self):
        self.write({"status": "closed"})

    @api.constrains("owner_id", "due_date")
    def _check_owner_due_date(self):
        for issue in self:
            if not issue.owner_id or not issue.due_date:
                raise ValidationError("Owner and due date are mandatory.")

    @api.model
    def cron_overdue_issue_checks(self):
        self.search([])._compute_is_overdue()
        for issue in self.search([("is_overdue", "=", True)]):
            issue.message_post(body="Compliance issue is overdue.")
            if issue.owner_id:
                issue.activity_schedule(
                    "mail.mail_activity_data_todo",
                    user_id=issue.owner_id.id,
                    summary="Overdue compliance issue",
                    note=issue.name,
                )
