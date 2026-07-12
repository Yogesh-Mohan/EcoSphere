from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ecosphere_auto_emission_calculation = fields.Boolean(
        string="Auto emission calculation",
        config_parameter="ecosphere_esg.auto_emission_calculation",
        default=True,
    )
    ecosphere_evidence_mandatory = fields.Boolean(
        string="Evidence mandatory for CSR approval",
        config_parameter="ecosphere_esg.evidence_mandatory",
        default=True,
    )
    ecosphere_badge_auto_award = fields.Boolean(
        string="Badge auto-award",
        config_parameter="ecosphere_esg.badge_auto_award",
        default=True,
    )
    ecosphere_environmental_weight = fields.Float(
        string="Environmental score weight",
        config_parameter="ecosphere_esg.environmental_weight",
        default=40.0,
    )
    ecosphere_social_weight = fields.Float(
        string="Social score weight",
        config_parameter="ecosphere_esg.social_weight",
        default=30.0,
    )
    ecosphere_governance_weight = fields.Float(
        string="Governance score weight",
        config_parameter="ecosphere_esg.governance_weight",
        default=30.0,
    )
    ecosphere_department_aggregation_method = fields.Selection(
        [
            ("average", "Average"),
            ("weighted_headcount", "Weighted by Headcount"),
            ("latest", "Latest Score"),
        ],
        string="Department aggregation method",
        config_parameter="ecosphere_esg.department_aggregation_method",
        default="average",
    )
    ecosphere_notification_preferences = fields.Selection(
        [("in_app", "In-app"), ("email", "Email"), ("both", "In-app and Email")],
        string="Notification preferences",
        config_parameter="ecosphere_esg.notification_preferences",
        default="in_app",
    )
    ecosphere_policy_reminder_interval = fields.Integer(
        string="Policy reminder interval (days)",
        config_parameter="ecosphere_esg.policy_reminder_interval",
        default=7,
    )
    ecosphere_compliance_overdue_reminder_interval = fields.Integer(
        string="Compliance overdue reminder interval (days)",
        config_parameter="ecosphere_esg.compliance_overdue_reminder_interval",
        default=3,
    )

    def set_values(self):
        self._validate_ecosphere_weights()
        return super().set_values()

    @api.constrains(
        "ecosphere_environmental_weight",
        "ecosphere_social_weight",
        "ecosphere_governance_weight",
    )
    def _check_ecosphere_weights(self):
        for settings in self:
            settings._validate_ecosphere_weights()

    def _validate_ecosphere_weights(self):
        total = (
            self.ecosphere_environmental_weight
            + self.ecosphere_social_weight
            + self.ecosphere_governance_weight
        )
        if round(total, 2) != 100.0:
            raise ValidationError("EcoSphere ESG score weights must total 100%.")
