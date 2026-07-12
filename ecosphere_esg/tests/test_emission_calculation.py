# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEmissionCalculation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.category = cls.env["esg.category"].create({
            "name": "Purchased Goods",
            "category_type": "emission",
            "company_id": cls.company.id,
        })
        cls.factor = cls.env["esg.emission.factor"].create({
            "name": "Purchased goods factor",
            "code": "PG-TEST",
            "activity_type": "product",
            "scope": "scope_3",
            "factor_value": 2.5,
            "input_unit": "unit",
            "output_unit": "kgCO2e",
            "category_id": cls.category.id,
            "company_id": cls.company.id,
        })

    def test_carbon_calculation_correctness(self):
        transaction = self.env["esg.carbon.transaction"].create({
            "company_id": self.company.id,
            "source_type": "manual",
            "emission_factor_id": self.factor.id,
            "activity_value": 10.0,
            "activity_unit": "unit",
            "conversion_multiplier": 1.2,
        })
        self.assertAlmostEqual(transaction.emission_kgco2e, 30.0, places=6)
        self.assertIn("30.000000 kgCO2e", transaction.calculation_details)

    def test_automatic_carbon_transaction_idempotency(self):
        vals = {
            "company_id": self.company.id,
            "source_type": "purchase",
            "source_model": "purchase.order",
            "source_res_id": 999,
            "source_line_reference": "line-1",
            "emission_factor_id": self.factor.id,
            "activity_value": 10.0,
            "activity_unit": "unit",
            "conversion_multiplier": 1.0,
            "state": "calculated",
        }
        first = self.env["esg.carbon.transaction"]._upsert_source_transaction(vals)
        second = self.env["esg.carbon.transaction"]._upsert_source_transaction(dict(vals, activity_value=12.0))

        self.assertEqual(first, second)
        self.assertEqual(second.activity_value, 12.0)
        count = self.env["esg.carbon.transaction"].search_count([
            ("source_model", "=", "purchase.order"),
            ("source_res_id", "=", 999),
            ("source_line_reference", "=", "line-1"),
            ("emission_factor_id", "=", self.factor.id),
        ])
        self.assertEqual(count, 1)

    def test_prevention_of_duplicate_source_transactions(self):
        values = {
            "company_id": self.company.id,
            "source_type": "purchase",
            "source_model": "purchase.order",
            "source_res_id": 1000,
            "source_line_reference": "line-duplicate",
            "emission_factor_id": self.factor.id,
            "activity_value": 5.0,
            "activity_unit": "unit",
            "conversion_multiplier": 1.0,
            "calculation_method": "automatic",
        }
        self.env["esg.carbon.transaction"].create(values)
        with self.assertRaises(ValidationError):
            self.env["esg.carbon.transaction"].create(dict(values, activity_value=6.0))

    def test_reduction_goal_progress(self):
        goal = self.env["esg.environmental.goal"].create({
            "name": "Reduce emissions",
            "company_id": self.company.id,
            "metric_type": "emissions",
            "goal_direction": "reduction",
            "baseline_value": 100.0,
            "baseline_year": 2024,
            "target_value": 60.0,
            "target_date": "2026-12-31",
            "current_value": 80.0,
        })
        self.assertAlmostEqual(goal.progress_percentage, 50.0, places=2)

    def test_increase_goal_progress(self):
        goal = self.env["esg.environmental.goal"].create({
            "name": "Increase recycling",
            "company_id": self.company.id,
            "metric_type": "recycling",
            "goal_direction": "increase",
            "baseline_value": 20.0,
            "baseline_year": 2024,
            "target_value": 80.0,
            "target_date": "2026-12-31",
            "current_value": 50.0,
        })
        self.assertAlmostEqual(goal.progress_percentage, 50.0, places=2)

    def test_product_esg_percentage_validation(self):
        product = self.env["product.template"].create({"name": "ESG Test Product"})
        with self.assertRaises(ValidationError):
            product.write({"esg_recycled_percentage": 120.0})

    def test_esg_weight_total_validation(self):
        with self.assertRaises(ValidationError):
            self.company.write({
                "esg_environmental_weight": 50.0,
                "esg_social_weight": 30.0,
                "esg_governance_weight": 30.0,
            })
