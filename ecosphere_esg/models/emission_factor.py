# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EsgEmissionFactor(models.Model):
    _name = "esg.emission.factor"
    _description = "ESG Emission Factor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "activity_type, scope, name"
    _check_company_auto = True

    name = fields.Char(required=True, tracking=True, index=True)
    code = fields.Char(required=True, tracking=True, index=True)
    activity_type = fields.Selection(
        selection=[
            ("product", "Product"),
            ("electricity", "Electricity"),
            ("fuel", "Fuel"),
            ("distance", "Distance"),
            ("manufacturing", "Manufacturing"),
            ("expense", "Expense"),
            ("waste", "Waste"),
            ("other", "Other"),
        ],
        required=True,
        tracking=True,
        index=True,
    )
    scope = fields.Selection(
        selection=[
            ("scope_1", "Scope 1"),
            ("scope_2", "Scope 2"),
            ("scope_3", "Scope 3"),
        ],
        required=True,
        tracking=True,
        index=True,
    )
    factor_value = fields.Float(required=True, tracking=True, digits=(16, 6))
    input_unit = fields.Char(required=True, tracking=True)
    output_unit = fields.Char(default="kgCO2e", required=True, tracking=True)
    source = fields.Char(tracking=True)
    source_url = fields.Char(string="Source URL / Reference", tracking=True)
    region = fields.Char(tracking=True)
    applicable_year = fields.Integer(tracking=True)
    valid_from = fields.Date(tracking=True)
    valid_to = fields.Date(tracking=True)
    category_id = fields.Many2one(
        comodel_name="esg.category",
        string="ESG Category",
        domain="[('category_type', '=', 'emission'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
        tracking=True,
    )
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
    )

    _sql_constraints = [
        ("code_company_uniq", "unique(code, company_id)", "The emission factor code must be unique per company."),
    ]

    @api.constrains("factor_value", "valid_from", "valid_to")
    def _check_factor_values(self):
        for factor in self:
            if factor.factor_value < 0:
                raise ValidationError(_("Emission factor value cannot be negative."))
            if factor.valid_from and factor.valid_to and factor.valid_to < factor.valid_from:
                raise ValidationError(_("Emission factor valid-to date cannot be before valid-from date."))

    @api.model
    def _select_active_factor(self, activity_type, company, date=None, scope=False, category=False, region=False):
        domain = [
            ("active", "=", True),
            ("activity_type", "=", activity_type),
            "|",
            ("company_id", "=", False),
            ("company_id", "=", company.id if company else self.env.company.id),
        ]
        if scope:
            domain.append(("scope", "=", scope))
        if category:
            domain.append(("category_id", "=", category.id))
        if region:
            domain += ["|", ("region", "=", False), ("region", "=", region)]
        if date:
            domain += ["|", ("valid_from", "=", False), ("valid_from", "<=", date)]
            domain += ["|", ("valid_to", "=", False), ("valid_to", ">=", date)]
        factors = self.search(domain, order="company_id desc, applicable_year desc, valid_from desc, id desc", limit=2)
        if not factors:
            return self.browse()
        if len(factors) > 1:
            raise ValidationError(_("More than one active emission factor matches this calculation. Narrow the factor configuration."))
        return factors
