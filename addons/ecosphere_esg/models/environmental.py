from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class CarbonTransaction(models.Model):
    _name = "ecosphere.carbon.transaction"
    _description = "Carbon Transaction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(string="Reference", default="/", readonly=True, tracking=True)
    date = fields.Date(default=fields.Date.context_today, required=True, tracking=True)
    department_id = fields.Many2one("hr.department", tracking=True)
    employee_id = fields.Many2one("hr.employee", tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, required=True)
    source_module = fields.Char()
    source_model = fields.Char(index=True)
    source_record_id = fields.Integer(index=True)
    source_record_display_name = fields.Char()
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
    activity_quantity = fields.Float(required=True, tracking=True)
    activity_unit = fields.Char(required=True, default="unit")
    emission_factor_id = fields.Many2one("ecosphere.emission.factor", required=True, tracking=True)
    emission_factor_value = fields.Float(readonly=True)
    emission_scope = fields.Selection(
        [("scope1", "Scope 1"), ("scope2", "Scope 2"), ("scope3", "Scope 3")],
        required=True,
    )
    co2e_value = fields.Float(string="CO2e value", compute="_compute_co2e", store=True, tracking=True)
    calculation_method = fields.Char(default="quantity x emission factor")
    auto_generated = fields.Boolean(default=False)
    verification_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("calculated", "Calculated"),
            ("verified", "Verified"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        tracking=True,
    )
    verified_by_id = fields.Many2one("res.users", readonly=True)
    verification_date = fields.Datetime(readonly=True)
    verification_notes = fields.Text()
    recalculation_note = fields.Text(readonly=True)

    _sql_constraints = [
        (
            "source_event_unique",
            "unique(source_model, source_record_id, activity_type, company_id)",
            "A carbon transaction already exists for this source event and activity.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = sequence.next_by_code("ecosphere.carbon.transaction") or "/"
            factor = self.env["ecosphere.emission.factor"].browse(vals.get("emission_factor_id"))
            if factor:
                vals.setdefault("emission_factor_value", factor.factor_value)
                vals.setdefault("emission_scope", factor.scope)
        records = super().create(vals_list)
        records.filtered(lambda rec: rec.verification_status == "draft").write({"verification_status": "calculated"})
        return records

    def write(self, vals):
        if "emission_factor_id" in vals:
            factor = self.env["ecosphere.emission.factor"].browse(vals["emission_factor_id"])
            vals["emission_factor_value"] = factor.factor_value
            vals["emission_scope"] = factor.scope
            vals["recalculation_note"] = "Emission factor changed on %s by %s." % (
                fields.Datetime.now(),
                self.env.user.display_name,
            )
        return super().write(vals)

    @api.depends("activity_quantity", "emission_factor_value")
    def _compute_co2e(self):
        for transaction in self:
            transaction.co2e_value = transaction.activity_quantity * transaction.emission_factor_value

    @api.constrains("activity_quantity")
    def _check_activity_quantity(self):
        for transaction in self:
            if transaction.activity_quantity < 0:
                raise ValidationError("Activity quantity cannot be negative.")

    @api.model
    def create_from_source(self, source_record, factor, quantity, activity_type=None, department=None, employee=None, module=None):
        if not source_record or not factor or not quantity:
            return self.browse()
        source_model = source_record._name
        source_record_id = source_record.id
        activity = activity_type or factor.activity_type
        source_company = source_record.company_id if "company_id" in source_record._fields else self.env.company
        existing = self.search([
            ("source_model", "=", source_model),
            ("source_record_id", "=", source_record_id),
            ("activity_type", "=", activity),
            ("company_id", "=", source_company.id),
        ], limit=1)
        vals = {
            "date": fields.Date.context_today(self),
            "department_id": department.id if department else False,
            "employee_id": employee.id if employee else False,
            "company_id": source_company.id,
            "source_module": module,
            "source_model": source_model,
            "source_record_id": source_record_id,
            "source_record_display_name": source_record.display_name,
            "activity_type": activity,
            "activity_quantity": quantity,
            "activity_unit": factor.input_unit,
            "emission_factor_id": factor.id,
            "emission_scope": factor.scope,
            "auto_generated": True,
        }
        if existing:
            existing.write(vals)
            return existing
        return self.create(vals)

    def action_verify(self):
        self.write({
            "verification_status": "verified",
            "verified_by_id": self.env.user.id,
            "verification_date": fields.Datetime.now(),
        })
        self.env["ecosphere.environmental.goal"].search([]).action_refresh_from_verified_carbon()

    def action_reject(self):
        self.write({"verification_status": "rejected"})

    def action_open_source_record(self):
        self.ensure_one()
        if not self.source_model or not self.source_record_id:
            raise UserError("This transaction is not linked to a source record.")
        return {
            "type": "ir.actions.act_window",
            "name": self.source_record_display_name or "Source Record",
            "res_model": self.source_model,
            "res_id": self.source_record_id,
            "view_mode": "form",
            "target": "current",
        }


class EsgActionRecommendation(models.Model):
    _name = "ecosphere.action.recommendation"
    _description = "ESG Action Centre Recommendation"
    _order = "severity desc, create_date desc"

    name = fields.Char(required=True)
    department_id = fields.Many2one("hr.department")
    severity = fields.Selection([("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")], default="medium")
    reason = fields.Text(required=True)
    recommended_action = fields.Text(required=True)
    source_model = fields.Char()
    source_record_id = fields.Integer()
    state = fields.Selection([("open", "Open"), ("done", "Done"), ("dismissed", "Dismissed")], default="open")

    def action_done(self):
        self.write({"state": "done"})

    def action_dismiss(self):
        self.write({"state": "dismissed"})

    @api.model
    def generate_recommendations(self):
        open_existing = self.search([("state", "=", "open")])
        open_existing.unlink()
        for goal in self.env["ecosphere.environmental.goal"].search([("status", "=", "at_risk")]):
            self.create({
                "name": "Environmental goal at risk",
                "department_id": goal.department_id.id,
                "severity": "high",
                "reason": "%s is below expected progress." % goal.name,
                "recommended_action": "Review verified carbon transactions and assign corrective actions to the department manager.",
                "source_model": goal._name,
                "source_record_id": goal.id,
            })
        for issue in self.env["ecosphere.compliance.issue"].search([("is_overdue", "=", True), ("severity", "in", ["high", "critical"])]):
            self.create({
                "name": "Critical overdue compliance issue",
                "department_id": issue.department_id.id,
                "severity": "critical",
                "reason": "%s is overdue." % issue.name,
                "recommended_action": "Escalate to the owner and ESG manager until evidence is submitted and verified.",
                "source_model": issue._name,
                "source_record_id": issue.id,
            })
