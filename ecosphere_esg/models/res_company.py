# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    esg_automatic_emission_calculation = fields.Boolean(
        string="Automatic Emission Calculation",
        default=True,
        help="Generate and reconcile carbon transactions from supported operational records.",
    )
    esg_csr_evidence_required = fields.Boolean(
        string="Require CSR Evidence",
        default=True,
        help="Require an attachment before CSR participation can be approved.",
    )
    esg_challenge_evidence_required = fields.Boolean(
        string="Require Challenge Evidence",
        default=True,
        help="Require an attachment before challenge participation can be approved.",
    )
    esg_automatic_badge_awarding = fields.Boolean(
        string="Automatic Badge Awarding",
        default=True,
        help="Periodically reconcile badge eligibility from structured badge rules.",
    )
    esg_notify_in_app = fields.Boolean(
        string="In-App Notifications",
        default=True,
    )
    esg_notify_email = fields.Boolean(
        string="Email Notifications",
        default=True,
    )
    esg_policy_reminder_days = fields.Integer(
        string="Policy Reminder Days",
        default=7,
        help="Days before acknowledgement deadline to send policy reminders.",
    )
    esg_compliance_warning_days = fields.Integer(
        string="Compliance Warning Days",
        default=7,
        help="Days before compliance due date to send warning reminders.",
    )
    esg_environmental_weight = fields.Float(
        string="Environmental Weight",
        default=40.0,
        digits=(16, 2),
    )
    esg_social_weight = fields.Float(
        string="Social Weight",
        default=30.0,
        digits=(16, 2),
    )
    esg_governance_weight = fields.Float(
        string="Governance Weight",
        default=30.0,
        digits=(16, 2),
    )
    esg_score_refresh_frequency = fields.Selection(
        selection=[
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
        string="Score Refresh Frequency",
        default="monthly",
        required=True,
    )
    esg_default_emission_unit = fields.Selection(
        selection=[
            ("kgco2e", "kgCO2e"),
            ("tco2e", "tCO2e"),
        ],
        string="Default Emission Unit",
        default="kgco2e",
        required=True,
    )
    esg_reporting_year = fields.Integer(
        string="Reporting Year",
        default=lambda self: fields.Date.context_today(self).year,
    )

    @api.constrains(
        "esg_environmental_weight",
        "esg_social_weight",
        "esg_governance_weight",
        "esg_policy_reminder_days",
        "esg_compliance_warning_days",
        "esg_reporting_year",
    )
    def _check_esg_configuration(self):
        for company in self:
            weights = (
                company.esg_environmental_weight,
                company.esg_social_weight,
                company.esg_governance_weight,
            )
            if any(weight < 0 for weight in weights):
                raise ValidationError(_("ESG score weights cannot be negative."))
            if abs(sum(weights) - 100.0) > 0.0001:
                raise ValidationError(_("Environmental, Social and Governance weights must total 100."))
            if company.esg_policy_reminder_days < 0:
                raise ValidationError(_("Policy reminder days cannot be negative."))
            if company.esg_compliance_warning_days < 0:
                raise ValidationError(_("Compliance warning days cannot be negative."))
            if company.esg_reporting_year and company.esg_reporting_year < 2000:
                raise ValidationError(_("ESG reporting year must be 2000 or later."))

    def _get_esg_weight_map(self):
        self.ensure_one()
        return {
            "environmental": self.esg_environmental_weight / 100.0,
            "social": self.esg_social_weight / 100.0,
            "governance": self.esg_governance_weight / 100.0,
        }
