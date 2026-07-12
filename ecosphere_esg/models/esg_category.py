# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EsgCategory(models.Model):
    _name = "esg.category"
    _description = "ESG Category"
    _order = "category_type, name"
    _check_company_auto = True

    name = fields.Char(required=True, translate=True, index=True)
    category_type = fields.Selection(
        selection=[
            ("csr_activity", "CSR Activity"),
            ("challenge", "Challenge"),
            ("emission", "Emission"),
            ("policy", "Policy"),
            ("training", "Training"),
        ],
        required=True,
        index=True,
    )
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        index=True,
    )

    _sql_constraints = [
        (
            "name_type_company_uniq",
            "unique(name, category_type, company_id)",
            "An ESG category with the same name and type already exists for this company.",
        ),
    ]

    @api.constrains("name")
    def _check_name(self):
        for category in self:
            if category.name and not category.name.strip():
                raise ValidationError(_("Category name cannot be empty."))
