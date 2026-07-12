from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        result = super().button_confirm()
        self._ecosphere_create_purchase_carbon()
        return result

    def _ecosphere_create_purchase_carbon(self):
        if self.env["ir.config_parameter"].sudo().get_param("ecosphere_esg.auto_emission_calculation", "True") in ("False", "0", ""):
            return
        Carbon = self.env["ecosphere.carbon.transaction"]
        Profile = self.env["ecosphere.product.esg.profile"]
        for order in self:
            for line in order.order_line:
                profile = Profile.search([("product_id", "=", line.product_id.id)], limit=1)
                if profile.default_emission_factor_id:
                    Carbon.create_from_source(
                        line,
                        profile.default_emission_factor_id,
                        line.product_qty,
                        department=False,
                        employee=False,
                        module="purchase",
                    )


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def button_mark_done(self):
        result = super().button_mark_done()
        self._ecosphere_create_mrp_carbon()
        return result

    def _ecosphere_create_mrp_carbon(self):
        if self.env["ir.config_parameter"].sudo().get_param("ecosphere_esg.auto_emission_calculation", "True") in ("False", "0", ""):
            return
        factor = self.env["ecosphere.emission.factor"].search([("activity_type", "=", "material")], limit=1)
        if not factor:
            return
        Carbon = self.env["ecosphere.carbon.transaction"]
        for production in self:
            Carbon.create_from_source(production, factor, production.product_qty, module="mrp")


class FleetVehicleLogServices(models.Model):
    _inherit = "fleet.vehicle.log.services"

    def write(self, vals):
        result = super().write(vals)
        self._ecosphere_create_fleet_carbon()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._ecosphere_create_fleet_carbon()
        return records

    def _ecosphere_create_fleet_carbon(self):
        if self.env["ir.config_parameter"].sudo().get_param("ecosphere_esg.auto_emission_calculation", "True") in ("False", "0", ""):
            return
        factor = self.env["ecosphere.emission.factor"].search([("activity_type", "=", "fuel")], limit=1)
        if not factor:
            return
        Carbon = self.env["ecosphere.carbon.transaction"]
        for service in self:
            quantity = service.amount or 0.0
            if quantity:
                Carbon.create_from_source(service, factor, quantity, module="fleet")


class HrExpense(models.Model):
    _inherit = "hr.expense"

    def action_submit_expenses(self):
        result = super().action_submit_expenses()
        self._ecosphere_create_expense_carbon()
        return result

    def _ecosphere_create_expense_carbon(self):
        if self.env["ir.config_parameter"].sudo().get_param("ecosphere_esg.auto_emission_calculation", "True") in ("False", "0", ""):
            return
        factor = self.env["ecosphere.emission.factor"].search([("activity_type", "=", "travel")], limit=1)
        if not factor:
            return
        Carbon = self.env["ecosphere.carbon.transaction"]
        for expense in self:
            employee = expense.employee_id
            department = employee.department_id
            Carbon.create_from_source(
                expense,
                factor,
                expense.quantity or 1.0,
                department=department,
                employee=employee,
                module="hr_expense",
            )
