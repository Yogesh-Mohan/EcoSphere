# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    esg_category_id = fields.Many2one(
        comodel_name="esg.category",
        string="ESG Category",
        domain="[('category_type', '=', 'emission'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
    )
    esg_emission_factor_id = fields.Many2one(
        comodel_name="esg.emission.factor",
        string="Emission Factor",
        domain="[('activity_type', 'in', ('product', 'manufacturing')), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
    )
    esg_carbon_value_per_unit = fields.Float(
        string="Carbon per Product Unit",
        digits=(16, 6),
        help="kgCO2e per standard product unit. Defaults from the emission factor but may be refined per product.",
    )
    esg_recycled_percentage = fields.Float(string="Recycled %", digits=(16, 2))
    esg_renewable_material_percentage = fields.Float(string="Renewable Material %", digits=(16, 2))
    esg_recyclable = fields.Boolean(string="Recyclable")
    esg_supplier_sustainability_rating = fields.Float(string="Supplier Sustainability Rating", digits=(16, 2))
    esg_notes = fields.Text(string="ESG Notes")

    @api.onchange("esg_emission_factor_id")
    def _onchange_esg_emission_factor_id(self):
        for product in self:
            if product.esg_emission_factor_id and not product.esg_carbon_value_per_unit:
                product.esg_carbon_value_per_unit = product.esg_emission_factor_id.factor_value

    @api.constrains(
        "esg_carbon_value_per_unit",
        "esg_recycled_percentage",
        "esg_renewable_material_percentage",
        "esg_supplier_sustainability_rating",
    )
    def _check_esg_profile_values(self):
        for product in self:
            if product.esg_carbon_value_per_unit < 0:
                raise ValidationError(_("Carbon per product unit cannot be negative."))
            percentage_values = {
                _("Recycled percentage"): product.esg_recycled_percentage,
                _("Renewable material percentage"): product.esg_renewable_material_percentage,
                _("Supplier sustainability rating"): product.esg_supplier_sustainability_rating,
            }
            for label, value in percentage_values.items():
                if value < 0 or value > 100:
                    raise ValidationError(_("%s must be between 0 and 100.") % label)
