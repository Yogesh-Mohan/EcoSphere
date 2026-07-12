# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare, float_round


class EsgEnvironmentalGoal(models.Model):
    _name = "esg.environmental.goal"
    _description = "ESG Environmental Goal"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "target_date, name"
    _check_company_auto = True

    name = fields.Char(required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, required=True, index=True, tracking=True)
    department_id = fields.Many2one("hr.department", check_company=True, tracking=True, index=True)
    metric_type = fields.Selection(
        selection=[
            ("emissions", "Emissions"),
            ("energy", "Energy"),
            ("water", "Water"),
            ("waste", "Waste"),
            ("renewable_energy", "Renewable Energy"),
            ("recycling", "Recycling"),
            ("other", "Other"),
        ],
        required=True,
        tracking=True,
    )
    goal_direction = fields.Selection(
        selection=[("reduction", "Reduction"), ("increase", "Increase")],
        required=True,
        default="reduction",
        tracking=True,
        help="Reduction goals improve as the current value decreases. Increase goals improve as the current value increases.",
    )
    baseline_value = fields.Float(required=True, tracking=True, digits=(16, 4))
    baseline_year = fields.Integer(required=True, tracking=True)
    target_value = fields.Float(required=True, tracking=True, digits=(16, 4))
    target_date = fields.Date(required=True, tracking=True)
    current_value = fields.Float(tracking=True, digits=(16, 4))
    progress_percentage = fields.Float(compute="_compute_progress_percentage", store=True, digits=(16, 2))
    status = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("active", "Active"),
            ("achieved", "Achieved"),
            ("missed", "Missed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    owner_id = fields.Many2one("hr.employee", check_company=True, tracking=True)
    description = fields.Text()

    @api.depends("baseline_value", "target_value", "current_value", "goal_direction")
    def _compute_progress_percentage(self):
        for goal in self:
            denominator = 0.0
            numerator = 0.0
            if goal.goal_direction == "reduction":
                denominator = goal.baseline_value - goal.target_value
                numerator = goal.baseline_value - goal.current_value
            elif goal.goal_direction == "increase":
                denominator = goal.target_value - goal.baseline_value
                numerator = goal.current_value - goal.baseline_value
            if denominator <= 0:
                goal.progress_percentage = 0.0
            else:
                progress = max(0.0, min(100.0, (numerator / denominator) * 100.0))
                goal.progress_percentage = float_round(progress, precision_digits=2)

    @api.constrains("baseline_value", "target_value", "current_value", "baseline_year", "target_date", "goal_direction", "company_id", "department_id", "owner_id")
    def _check_goal_values(self):
        today_year = fields.Date.context_today(self).year
        for goal in self:
            if goal.baseline_year < 2000 or goal.baseline_year > today_year + 10:
                raise ValidationError(_("Baseline year must be realistic for ESG reporting."))
            if goal.baseline_value < 0 or goal.target_value < 0 or goal.current_value < 0:
                raise ValidationError(_("Environmental goal values cannot be negative."))
            if goal.goal_direction == "reduction" and float_compare(goal.target_value, goal.baseline_value, precision_digits=4) >= 0:
                raise ValidationError(_("Reduction goals must have a target value below the baseline value."))
            if goal.goal_direction == "increase" and float_compare(goal.target_value, goal.baseline_value, precision_digits=4) <= 0:
                raise ValidationError(_("Increase goals must have a target value above the baseline value."))
            if goal.department_id.company_id and goal.department_id.company_id != goal.company_id:
                raise ValidationError(_("The goal department must belong to the goal company."))
            if goal.owner_id.company_id and goal.owner_id.company_id != goal.company_id:
                raise ValidationError(_("The goal owner must belong to the goal company."))

    def action_activate(self):
        self.write({"status": "active"})

    def action_mark_achieved(self):
        for goal in self:
            if goal.progress_percentage < 100:
                raise ValidationError(_("Only goals with 100% progress can be marked achieved."))
        self.write({"status": "achieved"})

    def action_mark_missed(self):
        self.write({"status": "missed"})

    def action_cancel(self):
        self.write({"status": "cancelled"})
