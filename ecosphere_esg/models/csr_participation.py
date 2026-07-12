# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class EsgCsrParticipation(models.Model):
    _name = "esg.csr.participation"
    _description = "ESG CSR Participation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "completion_date desc, id desc"
    _check_company_auto = True

    activity_id = fields.Many2one("esg.csr.activity", required=True, ondelete="restrict", check_company=True, tracking=True, index=True)
    company_id = fields.Many2one(related="activity_id.company_id", store=True, readonly=True)
    employee_id = fields.Many2one("hr.employee", required=True, check_company=True, tracking=True, index=True)
    department_id = fields.Many2one(related="employee_id.department_id", store=True, readonly=True, index=True)
    proof_attachment_ids = fields.Many2many(
        "ir.attachment",
        "esg_csr_participation_attachment_rel",
        "participation_id",
        "attachment_id",
        string="Proof Attachments",
        copy=False,
    )
    proof_description = fields.Text()
    participation_hours = fields.Float(digits=(16, 2), tracking=True)
    completion_date = fields.Date(tracking=True)
    state = fields.Selection(
        selection=[
            ("registered", "Registered"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="registered",
        required=True,
        tracking=True,
        index=True,
    )
    reviewer_id = fields.Many2one("hr.employee", check_company=True, tracking=True)
    review_date = fields.Datetime(readonly=True, tracking=True)
    rejection_reason = fields.Text(tracking=True)
    points_earned = fields.Float(readonly=True, digits=(16, 2), tracking=True)
    xp_ledger_id = fields.Many2one("esg.xp.ledger", readonly=True, copy=False)
    reversal_ledger_id = fields.Many2one("esg.xp.ledger", readonly=True, copy=False)

    _sql_constraints = [
        ("activity_employee_uniq", "unique(activity_id, employee_id)", "An employee can participate only once in the same CSR activity."),
    ]

    def write(self, vals):
        protected_fields = {
            "reviewer_id",
            "review_date",
            "points_earned",
            "xp_ledger_id",
            "reversal_ledger_id",
        }
        if vals.get("state") in ("approved", "rejected"):
            protected_fields.add("state")
        if protected_fields & set(vals) and not self.env.context.get("esg_internal_review_write"):
            if not self.env.user.has_group("ecosphere_esg.group_esg_officer") and not self.env.user.has_group("ecosphere_esg.group_esg_administrator"):
                raise UserError(_("Only authorized ESG reviewers can update CSR review results."))
        return super().write(vals)

    @api.constrains("activity_id", "employee_id", "participation_hours", "reviewer_id")
    def _check_participation_values(self):
        for participation in self:
            if participation.employee_id.company_id and participation.employee_id.company_id != participation.company_id:
                raise ValidationError(_("The participant must belong to the activity company."))
            if participation.reviewer_id.company_id and participation.reviewer_id.company_id != participation.company_id:
                raise ValidationError(_("The reviewer must belong to the activity company."))
            if participation.participation_hours < 0:
                raise ValidationError(_("Participation hours cannot be negative."))

    def action_submit(self):
        for participation in self:
            if participation.state not in ("registered", "rejected"):
                raise UserError(_("Only registered or rejected CSR participation can be submitted."))
            participation.write({
                "state": "submitted",
                "completion_date": participation.completion_date or fields.Date.context_today(participation),
                "rejection_reason": False,
            })

    def action_approve(self):
        reviewer = self.env.user.employee_id
        for participation in self:
            participation._validate_can_approve()
            if participation.xp_ledger_id:
                raise UserError(_("This participation has already awarded points."))
            points = participation.activity_id.points
            ledger = self.env["esg.xp.ledger"].create_entry(
                participation.employee_id,
                "csr_approval",
                points,
                points,
                participation,
                _("CSR participation approved: %s") % participation.activity_id.title,
            )
            participation.with_context(esg_internal_review_write=True).write({
                "state": "approved",
                "reviewer_id": reviewer.id if reviewer else False,
                "review_date": fields.Datetime.now(),
                "points_earned": points,
                "xp_ledger_id": ledger.id,
                "rejection_reason": False,
            })

    def action_reject(self):
        for participation in self:
            if not participation.rejection_reason:
                raise UserError(_("A rejection reason is required."))
            participation.with_context(esg_internal_review_write=True).write({
                "state": "rejected",
                "review_date": fields.Datetime.now(),
                "reviewer_id": self.env.user.employee_id.id if self.env.user.employee_id else False,
            })

    def action_reverse_approval(self):
        for participation in self:
            if participation.state != "approved" or not participation.xp_ledger_id:
                raise UserError(_("Only approved participation with a ledger entry can be reversed."))
            if participation.reversal_ledger_id:
                raise UserError(_("This approval has already been reversed."))
            reversal = self.env["esg.xp.ledger"].create_entry(
                participation.employee_id,
                "reversal",
                -participation.xp_ledger_id.xp_amount,
                -participation.xp_ledger_id.points_amount,
                participation,
                _("Reversal of CSR approval: %s") % participation.activity_id.title,
                reversal_of=participation.xp_ledger_id,
            )
            participation.with_context(esg_internal_review_write=True).write({
                "state": "submitted",
                "points_earned": 0.0,
                "reversal_ledger_id": reversal.id,
            })

    def _validate_can_approve(self):
        self.ensure_one()
        if self.state != "submitted":
            raise UserError(_("Only submitted CSR participation can be approved."))
        if self.company_id.esg_csr_evidence_required and not self.proof_attachment_ids:
            raise ValidationError(_("Evidence is required before this CSR participation can be approved."))
        if self.participation_hours <= 0:
            raise ValidationError(_("Participation hours must be greater than zero before approval."))
