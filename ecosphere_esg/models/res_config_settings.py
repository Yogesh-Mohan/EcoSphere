# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    esg_automatic_emission_calculation = fields.Boolean(
        related="company_id.esg_automatic_emission_calculation",
        readonly=False,
    )
    esg_csr_evidence_required = fields.Boolean(
        related="company_id.esg_csr_evidence_required",
        readonly=False,
    )
    esg_challenge_evidence_required = fields.Boolean(
        related="company_id.esg_challenge_evidence_required",
        readonly=False,
    )
    esg_automatic_badge_awarding = fields.Boolean(
        related="company_id.esg_automatic_badge_awarding",
        readonly=False,
    )
    esg_notify_in_app = fields.Boolean(
        related="company_id.esg_notify_in_app",
        readonly=False,
    )
    esg_notify_email = fields.Boolean(
        related="company_id.esg_notify_email",
        readonly=False,
    )
    esg_policy_reminder_days = fields.Integer(
        related="company_id.esg_policy_reminder_days",
        readonly=False,
    )
    esg_compliance_warning_days = fields.Integer(
        related="company_id.esg_compliance_warning_days",
        readonly=False,
    )
    esg_environmental_weight = fields.Float(
        related="company_id.esg_environmental_weight",
        readonly=False,
    )
    esg_social_weight = fields.Float(
        related="company_id.esg_social_weight",
        readonly=False,
    )
    esg_governance_weight = fields.Float(
        related="company_id.esg_governance_weight",
        readonly=False,
    )
    esg_score_refresh_frequency = fields.Selection(
        related="company_id.esg_score_refresh_frequency",
        readonly=False,
    )
    esg_default_emission_unit = fields.Selection(
        related="company_id.esg_default_emission_unit",
        readonly=False,
    )
    esg_reporting_year = fields.Integer(
        related="company_id.esg_reporting_year",
        readonly=False,
    )
