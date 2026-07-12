from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EsgCategory(models.Model):
    _name = "ecosphere.esg.category"
    _description = "ESG Category"
    _order = "category_type, name"

    name = fields.Char(required=True)
    category_type = fields.Selection(
        [
            ("csr", "CSR"),
            ("challenge", "Challenge"),
            ("environmental", "Environmental"),
            ("governance", "Governance"),
        ],
        required=True,
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    active = fields.Boolean(default=True)


class EmissionFactor(models.Model):
    _name = "ecosphere.emission.factor"
    _description = "Emission Factor"
    _order = "scope, name"

    name = fields.Char(required=True)
    activity_type = fields.Selection(
        [
            ("electricity", "Electricity"),
            ("fuel", "Fuel"),
            ("material", "Material"),
            ("travel", "Travel"),
            ("waste", "Waste"),
            ("service", "Service"),
            ("other", "Other"),
        ],
        required=True,
    )
    source_module = fields.Char()
    scope = fields.Selection(
        [("scope1", "Scope 1"), ("scope2", "Scope 2"), ("scope3", "Scope 3")],
        required=True,
    )
    factor_value = fields.Float(required=True)
    input_unit = fields.Char(required=True, default="unit")
    output_unit = fields.Char(required=True, default="kgCO2e")
    valid_from = fields.Date()
    valid_until = fields.Date()
    reference = fields.Char(string="Reference/source")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    @api.constrains("factor_value")
    def _check_factor_value(self):
        for factor in self:
            if factor.factor_value < 0:
                raise ValidationError("Emission factor value cannot be negative.")


class ProductEsgProfile(models.Model):
    _name = "ecosphere.product.esg.profile"
    _description = "Product ESG Profile"
    _rec_name = "product_id"

    product_id = fields.Many2one("product.product", required=True, ondelete="cascade")
    default_emission_factor_id = fields.Many2one("ecosphere.emission.factor")
    recycled_material_percentage = fields.Float()
    sustainable_certification = fields.Char()
    supplier_sustainability_rating = fields.Selection(
        [("a", "A"), ("b", "B"), ("c", "C"), ("d", "D"), ("unknown", "Unknown")],
        default="unknown",
    )
    notes = fields.Text()

    _sql_constraints = [
        ("product_unique", "unique(product_id)", "A product can have only one ESG profile."),
    ]

    @api.constrains("recycled_material_percentage")
    def _check_recycled_percentage(self):
        for profile in self:
            if not 0 <= profile.recycled_material_percentage <= 100:
                raise ValidationError("Recycled material percentage must be between 0 and 100.")


class EnvironmentalGoal(models.Model):
    _name = "ecosphere.environmental.goal"
    _description = "Environmental Goal"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "end_date, name"

    name = fields.Char(required=True, tracking=True)
    department_id = fields.Many2one("hr.department", required=True, tracking=True)
    metric = fields.Selection(
        [
            ("co2e", "CO2e"),
            ("energy", "Energy"),
            ("water", "Water"),
            ("waste", "Waste"),
            ("recycling", "Recycling"),
        ],
        required=True,
        default="co2e",
    )
    baseline_value = fields.Float(required=True, tracking=True)
    target_value = fields.Float(required=True, tracking=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    current_value = fields.Float(tracking=True)
    progress_percentage = fields.Float(compute="_compute_progress", store=True)
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("on_track", "On Track"),
            ("at_risk", "At Risk"),
            ("achieved", "Achieved"),
            ("missed", "Missed"),
        ],
        default="draft",
        tracking=True,
    )

    @api.depends("baseline_value", "target_value", "current_value")
    def _compute_progress(self):
        for goal in self:
            span = goal.baseline_value - goal.target_value
            if not span:
                goal.progress_percentage = 100.0 if goal.current_value <= goal.target_value else 0.0
            else:
                goal.progress_percentage = max(0.0, min(100.0, ((goal.baseline_value - goal.current_value) / span) * 100.0))

    def action_refresh_from_verified_carbon(self):
        Carbon = self.env["ecosphere.carbon.transaction"]
        for goal in self.filtered(lambda item: item.metric == "co2e"):
            domain = [
                ("department_id", "=", goal.department_id.id),
                ("verification_status", "=", "verified"),
            ]
            if goal.start_date:
                domain.append(("date", ">=", goal.start_date))
            if goal.end_date:
                domain.append(("date", "<=", goal.end_date))
            rows = Carbon.read_group(domain, ["co2e_value:sum"], [])
            goal.current_value = rows[0]["co2e_value"] if rows else 0.0
            if goal.current_value <= goal.target_value:
                goal.status = "achieved"
            elif goal.progress_percentage >= 75:
                goal.status = "on_track"
            else:
                goal.status = "at_risk"


class EsgPolicy(models.Model):
    _name = "ecosphere.esg.policy"
    _description = "ESG Policy"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "policy_code, version desc"

    name = fields.Char(string="Policy title", required=True, tracking=True)
    policy_code = fields.Char(required=True, tracking=True)
    version = fields.Char(required=True, default="1.0", tracking=True)
    category_id = fields.Many2one("ecosphere.esg.category", domain=[("category_type", "=", "governance")])
    description = fields.Html()
    attachment = fields.Binary()
    attachment_filename = fields.Char()
    publish_date = fields.Date()
    effective_date = fields.Date()
    review_date = fields.Date(string="Expiry/review date")
    applicable_department_ids = fields.Many2many("hr.department", string="Applicable departments")
    applicable_employee_ids = fields.Many2many("hr.employee", string="Applicable employees")
    owner_id = fields.Many2one("res.users", string="Responsible owner", default=lambda self: self.env.user)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("published", "Published"),
            ("expired", "Expired"),
            ("archived", "Archived"),
        ],
        default="draft",
        tracking=True,
    )

    _sql_constraints = [
        ("policy_version_unique", "unique(policy_code, version)", "Policy code and version must be unique."),
    ]

    def action_publish(self):
        today = fields.Date.context_today(self)
        for policy in self:
            policy.write({"state": "published", "publish_date": policy.publish_date or today})
            policy._create_acknowledgements()

    def action_archive(self):
        self.write({"state": "archived"})

    def action_expire(self):
        self.write({"state": "expired"})

    def _target_employees(self):
        self.ensure_one()
        Employee = self.env["hr.employee"]
        if self.applicable_employee_ids:
            return self.applicable_employee_ids
        domain = []
        if self.applicable_department_ids:
            domain = [("department_id", "in", self.applicable_department_ids.ids)]
        return Employee.search(domain)

    def _create_acknowledgements(self):
        Ack = self.env["ecosphere.policy.acknowledgement"]
        for policy in self:
            for employee in policy._target_employees():
                Ack.create_if_missing(policy, employee)


class Badge(models.Model):
    _name = "ecosphere.badge"
    _description = "EcoSphere Badge"

    name = fields.Char(required=True)
    description = fields.Text()
    icon = fields.Binary()
    metric = fields.Selection(
        [
            ("xp", "XP"),
            ("completed_challenges", "Completed challenges"),
            ("csr_participation", "CSR participation"),
            ("policy_completion", "Policy completion"),
        ],
        required=True,
    )
    operator = fields.Selection(
        [(">=", ">="), (">", ">"), ("=", "="), ("<=", "<="), ("<", "<")],
        required=True,
        default=">=",
    )
    threshold = fields.Float(required=True)
    active = fields.Boolean(default=True)

    def _compare(self, value):
        self.ensure_one()
        if self.operator == ">=":
            return value >= self.threshold
        if self.operator == ">":
            return value > self.threshold
        if self.operator == "=":
            return value == self.threshold
        if self.operator == "<=":
            return value <= self.threshold
        return value < self.threshold


class Reward(models.Model):
    _name = "ecosphere.reward"
    _description = "EcoSphere Reward"

    name = fields.Char(required=True)
    description = fields.Text()
    image = fields.Binary()
    points_required = fields.Float(required=True)
    available_stock = fields.Integer(required=True, default=0)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
