from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class CsrActivity(models.Model):
    _name = "ecosphere.csr.activity"
    _description = "CSR Activity"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_date desc"

    name = fields.Char(string="Title", required=True, tracking=True)
    category_id = fields.Many2one("ecosphere.esg.category", domain=[("category_type", "=", "csr")])
    description = fields.Html()
    organizer_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    department_id = fields.Many2one("hr.department")
    start_date = fields.Datetime(required=True)
    end_date = fields.Datetime(required=True)
    maximum_participants = fields.Integer(default=0)
    evidence_required = fields.Boolean(default=True)
    points = fields.Float(default=10.0)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("open", "Open"),
            ("ongoing", "Ongoing"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )
    participation_ids = fields.One2many("ecosphere.csr.participation", "activity_id")
    approved_count = fields.Integer(compute="_compute_counts")

    def _compute_counts(self):
        for activity in self:
            activity.approved_count = len(activity.participation_ids.filtered(lambda item: item.approval_status == "approved"))

    def action_open(self):
        self.write({"state": "open"})

    def action_complete(self):
        self.write({"state": "completed"})


class CsrParticipation(models.Model):
    _name = "ecosphere.csr.participation"
    _description = "CSR Participation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "registration_date desc"

    activity_id = fields.Many2one("ecosphere.csr.activity", required=True, ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", required=True)
    department_id = fields.Many2one(related="employee_id.department_id", store=True)
    registration_date = fields.Datetime(default=fields.Datetime.now, required=True)
    completion_date = fields.Datetime()
    proof_attachment = fields.Binary()
    proof_filename = fields.Char()
    employee_notes = fields.Text()
    reviewer_notes = fields.Text()
    approval_status = fields.Selection(
        [
            ("registered", "Registered"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="registered",
        tracking=True,
    )
    points_awarded = fields.Float(readonly=True)
    points_transaction_id = fields.Many2one("ecosphere.points.transaction", readonly=True)

    _sql_constraints = [
        ("csr_employee_unique", "unique(activity_id, employee_id)", "The employee is already registered for this CSR activity."),
    ]

    def action_submit(self):
        self.write({"approval_status": "submitted", "completion_date": fields.Datetime.now()})

    def action_approve(self):
        evidence_mandatory = self.env["ir.config_parameter"].sudo().get_param("ecosphere_esg.evidence_mandatory", "True") not in ("False", "0", "")
        for participation in self:
            if evidence_mandatory and participation.activity_id.evidence_required and not participation.proof_attachment:
                raise UserError("Proof attachment is required before approval.")
            if not participation.points_transaction_id:
                tx = self.env["ecosphere.points.transaction"].create({
                    "employee_id": participation.employee_id.id,
                    "points": participation.activity_id.points,
                    "reason": "CSR approval: %s" % participation.activity_id.name,
                    "source_model": participation._name,
                    "source_record_id": participation.id,
                })
                participation.points_transaction_id = tx.id
                participation.points_awarded = participation.activity_id.points
            participation.approval_status = "approved"
            participation.employee_id.message_post(body="CSR participation approved: %s" % participation.activity_id.name)

    def action_reject(self):
        self.write({"approval_status": "rejected"})
        for participation in self:
            participation.employee_id.message_post(body="CSR participation rejected: %s" % participation.activity_id.name)


class Challenge(models.Model):
    _name = "ecosphere.challenge"
    _description = "EcoSphere Challenge"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "deadline"

    name = fields.Char(string="Title", required=True, tracking=True)
    category_id = fields.Many2one("ecosphere.esg.category", domain=[("category_type", "=", "challenge")])
    description = fields.Html()
    xp = fields.Float(default=20.0)
    difficulty = fields.Selection([("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")], default="easy")
    evidence_required = fields.Boolean(default=True)
    start_date = fields.Date(required=True)
    deadline = fields.Date(required=True)
    responsible_manager_id = fields.Many2one("res.users")
    applicable_department_ids = fields.Many2many("hr.department")
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("under_review", "Under Review"),
            ("completed", "Completed"),
            ("archived", "Archived"),
        ],
        default="draft",
        tracking=True,
    )

    def action_activate(self):
        self.write({"status": "active"})


class ChallengeParticipation(models.Model):
    _name = "ecosphere.challenge.participation"
    _description = "Challenge Participation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "submission_date desc"

    challenge_id = fields.Many2one("ecosphere.challenge", required=True, ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", required=True)
    department_id = fields.Many2one(related="employee_id.department_id", store=True)
    progress_percentage = fields.Float(default=0.0)
    proof = fields.Binary()
    proof_filename = fields.Char()
    submission_date = fields.Datetime()
    approval_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        tracking=True,
    )
    reviewer_id = fields.Many2one("res.users")
    review_comments = fields.Text()
    xp_awarded = fields.Float(readonly=True)
    points_transaction_id = fields.Many2one("ecosphere.points.transaction", readonly=True)

    _sql_constraints = [
        ("challenge_employee_unique", "unique(challenge_id, employee_id)", "The employee already joined this challenge."),
    ]

    @api.constrains("progress_percentage")
    def _check_progress(self):
        for participation in self:
            if not 0 <= participation.progress_percentage <= 100:
                raise ValidationError("Progress must be between 0 and 100.")

    def action_submit(self):
        self.write({"approval_state": "submitted", "submission_date": fields.Datetime.now(), "progress_percentage": 100.0})

    def action_approve(self):
        for participation in self:
            if participation.challenge_id.evidence_required and not participation.proof:
                raise UserError("Proof is required before challenge approval.")
            if not participation.points_transaction_id:
                tx = self.env["ecosphere.points.transaction"].create({
                    "employee_id": participation.employee_id.id,
                    "points": participation.challenge_id.xp,
                    "reason": "Challenge approval: %s" % participation.challenge_id.name,
                    "source_model": participation._name,
                    "source_record_id": participation.id,
                })
                participation.points_transaction_id = tx.id
                participation.xp_awarded = participation.challenge_id.xp
            participation.write({"approval_state": "approved", "reviewer_id": self.env.user.id})
            participation.employee_id.message_post(body="Challenge approved: %s" % participation.challenge_id.name)

    def action_reject(self):
        self.write({"approval_state": "rejected", "reviewer_id": self.env.user.id})
        for participation in self:
            participation.employee_id.message_post(body="Challenge rejected: %s" % participation.challenge_id.name)
