# -*- coding: utf-8 -*-

from odoo import api, models, _


class EsgSourceIntegrationServiceBase(models.AbstractModel):
    _name = "esg.source.integration.service"
    _description = "ESG Source Integration Service"

    @api.model
    def sync_purchase_order(self, purchase_order):
        if not purchase_order.company_id.esg_automatic_emission_calculation:
            return self.env["esg.carbon.transaction"].browse()
        transactions = self.env["esg.carbon.transaction"]
        for line in purchase_order.order_line.filtered(lambda line: line.product_id and not line.display_type):
            product = line.product_id.product_tmpl_id
            factor = product.esg_emission_factor_id
            if not factor:
                continue
            quantity = line.qty_received or line.product_qty
            if quantity <= 0:
                continue
            transactions |= transactions._upsert_source_transaction({
                "date": purchase_order.date_order.date() if purchase_order.date_order else purchase_order.create_date.date(),
                "company_id": purchase_order.company_id.id,
                "source_type": "purchase",
                "source_model": purchase_order._name,
                "source_res_id": purchase_order.id,
                "source_line_reference": str(line.id),
                "emission_factor_id": factor.id,
                "activity_value": quantity,
                "activity_unit": line.product_uom.name,
                "conversion_multiplier": 1.0,
                "state": "calculated",
                "notes": _("Generated from confirmed purchase order %s.") % purchase_order.name,
            })
        return transactions

    @api.model
    def sync_manufacturing_order(self, production):
        if not production.company_id.esg_automatic_emission_calculation:
            return self.env["esg.carbon.transaction"].browse()
        product = production.product_id.product_tmpl_id
        factor = product.esg_emission_factor_id
        if not factor:
            return self.env["esg.carbon.transaction"].browse()
        quantity = production.product_qty or 0.0
        if quantity <= 0:
            return self.env["esg.carbon.transaction"].browse()
        return self.env["esg.carbon.transaction"]._upsert_source_transaction({
            "date": production.date_finished.date() if production.date_finished else self.env.context.get("date") or production.create_date.date(),
            "company_id": production.company_id.id,
            "source_type": "manufacturing",
            "source_model": production._name,
            "source_res_id": production.id,
            "source_line_reference": "finished_product",
            "emission_factor_id": factor.id,
            "activity_value": quantity,
            "activity_unit": production.product_uom_id.name,
            "conversion_multiplier": 1.0,
            "state": "calculated",
            "notes": _("Generated from manufacturing order %s.") % production.name,
        })


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        res = super().button_confirm()
        self.env["esg.source.integration.service"].sudo()._sync_confirmed_purchases(self)
        return res


class EsgSourceIntegrationServicePurchase(models.AbstractModel):
    _inherit = "esg.source.integration.service"

    @api.model
    def _sync_confirmed_purchases(self, purchase_orders):
        for order in purchase_orders.filtered(lambda order: order.state in ("purchase", "done")):
            self.sync_purchase_order(order)
