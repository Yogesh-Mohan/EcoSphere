# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round


class EsgCarbonTransaction(models.Model):
    _name = "esg.carbon.transaction"
    _description = "ESG Carbon Transaction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, reference desc"
    _check_company_auto = True

    reference = fields.Char(default="New", required=True, copy=False, readonly=True, tracking=True)
    date = fields.Date(default=fields.Date.context_today, required=True, tracking=True, index=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, required=True, index=True, tracking=True)
    department_id = fields.Many2one("hr.department", check_company=True, tracking=True, index=True)
    employee_id = fields.Many2one("hr.employee", check_company=True, tracking=True, index=True)
    source_type = fields.Selection(
        selection=[
            ("purchase", "Purchase"),
            ("manufacturing", "Manufacturing"),
            ("expense", "Expense"),
            ("fleet", "Fleet"),
            ("manual", "Manual"),
            ("import", "Import"),
            ("other", "Other"),
        ],
        required=True,
        default="manual",
        tracking=True,
        index=True,
    )
    source_model = fields.Char(index=True, tracking=True)
    source_res_id = fields.Integer(index=True, tracking=True)
    source_line_reference = fields.Char(index=True, tracking=True)
    emission_factor_id = fields.Many2one("esg.emission.factor", required=True, check_company=True, tracking=True, index=True)
    activity_value = fields.Float(required=True, tracking=True, digits=(16, 6))
    activity_unit = fields.Char(required=True, tracking=True)
    conversion_multiplier = fields.Float(default=1.0, required=True, tracking=True, digits=(16, 6))
    emission_kgco2e = fields.Float(compute="_compute_emission_kgco2e", store=True, readonly=False, tracking=True, digits=(16, 6))
    scope = fields.Selection(related="emission_factor_id.scope", store=True, readonly=True, tracking=True)
    category_id = fields.Many2one(related="emission_factor_id.category_id", store=True, readonly=True)
    calculation_method = fields.Selection(
        selection=[("automatic", "Automatic"), ("manual", "Manual"), ("imported", "Imported")],
        default="manual",
        required=True,
        tracking=True,
        index=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("calculated", "Calculated"),
            ("validated", "Validated"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    calculation_details = fields.Text(readonly=True, tracking=True)
    notes = fields.Text()

    @api.depends("activity_value", "emission_factor_id.factor_value", "conversion_multiplier")
    def _compute_emission_kgco2e(self):
        for transaction in self:
            factor = transaction.emission_factor_id.factor_value if transaction.emission_factor_id else 0.0
            value = transaction.activity_value * factor * transaction.conversion_multiplier
            transaction.emission_kgco2e = float_round(value, precision_digits=6)

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("reference", "New") == "New":
                vals["reference"] = sequence.next_by_code("esg.carbon.transaction") or "New"
        records = super().create(vals_list)
        records._update_calculation_details()
        return records

    def write(self, vals):
        res = super().write(vals)
        if {"activity_value", "emission_factor_id", "conversion_multiplier", "activity_unit"} & set(vals):
            self._update_calculation_details()
        return res

    def unlink(self):
        if any(record.state == "validated" for record in self):
            raise UserError(_("Validated carbon transactions cannot be deleted. Cancel them instead."))
        return super().unlink()

    @api.constrains("activity_value", "conversion_multiplier", "company_id", "department_id", "employee_id")
    def _check_transaction_values(self):
        for transaction in self:
            if transaction.activity_value < 0:
                raise ValidationError(_("Activity value cannot be negative."))
            if transaction.conversion_multiplier <= 0:
                raise ValidationError(_("Conversion multiplier must be greater than zero."))
            if transaction.department_id.company_id and transaction.department_id.company_id != transaction.company_id:
                raise ValidationError(_("The transaction department must belong to the transaction company."))
            if transaction.employee_id.company_id and transaction.employee_id.company_id != transaction.company_id:
                raise ValidationError(_("The transaction employee must belong to the transaction company."))

    @api.constrains("calculation_method", "source_model", "source_res_id", "source_line_reference", "emission_factor_id", "company_id")
    def _check_unique_automatic_source(self):
        for transaction in self:
            if transaction.calculation_method != "automatic":
                continue
            if not transaction.source_model or not transaction.source_res_id or not transaction.source_line_reference:
                raise ValidationError(_("Automatic carbon transactions require a complete source identity."))
            duplicate = self.search_count([
                ("id", "!=", transaction.id),
                ("calculation_method", "=", "automatic"),
                ("company_id", "=", transaction.company_id.id),
                ("source_model", "=", transaction.source_model),
                ("source_res_id", "=", transaction.source_res_id),
                ("source_line_reference", "=", transaction.source_line_reference),
                ("emission_factor_id", "=", transaction.emission_factor_id.id),
                ("state", "!=", "cancelled"),
            ])
            if duplicate:
                raise ValidationError(_("A carbon transaction already exists for this source line and emission factor."))

    def _update_calculation_details(self):
        for transaction in self:
            if not transaction.emission_factor_id:
                continue
            transaction.calculation_details = _(
                "%(activity_value).6f %(activity_unit)s x %(factor).6f %(output_unit)s/%(input_unit)s x %(multiplier).6f = %(emission).6f kgCO2e"
            ) % {
                "activity_value": transaction.activity_value,
                "activity_unit": transaction.activity_unit or "unit",
                "factor": transaction.emission_factor_id.factor_value,
                "output_unit": transaction.emission_factor_id.output_unit or "kgCO2e",
                "input_unit": transaction.emission_factor_id.input_unit or transaction.activity_unit or "unit",
                "multiplier": transaction.conversion_multiplier,
                "emission": transaction.emission_kgco2e,
            }

    @api.model
    def _upsert_source_transaction(self, vals):
        required = ["company_id", "source_model", "source_res_id", "source_line_reference", "emission_factor_id"]
        missing = [field for field in required if not vals.get(field)]
        if missing:
            raise ValidationError(_("Missing source identity values for automatic carbon transaction: %s") % ", ".join(missing))
        vals = dict(vals, calculation_method="automatic")
        domain = [
            ("company_id", "=", vals["company_id"]),
            ("source_model", "=", vals["source_model"]),
            ("source_res_id", "=", vals["source_res_id"]),
            ("source_line_reference", "=", vals["source_line_reference"]),
            ("emission_factor_id", "=", vals["emission_factor_id"]),
            ("calculation_method", "=", "automatic"),
            ("state", "!=", "cancelled"),
        ]
        transaction = self.search(domain, limit=1)
        if transaction:
            if transaction.state == "validated":
                vals.pop("state", None)
            transaction.write(vals)
            return transaction
        return self.create(vals)

    def action_calculate(self):
        self._update_calculation_details()
        self.write({"state": "calculated"})

    def action_validate(self):
        for transaction in self:
            if transaction.emission_kgco2e < 0:
                raise ValidationError(_("Calculated emissions cannot be negative."))
        self.write({"state": "validated"})

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_open_source_record(self):
        self.ensure_one()
        if not self.source_model or not self.source_res_id:
            raise UserError(_("This carbon transaction is not linked to a source record."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Source Record"),
            "res_model": self.source_model,
            "res_id": self.source_res_id,
            "view_mode": "form",
            "target": "current",
        }
