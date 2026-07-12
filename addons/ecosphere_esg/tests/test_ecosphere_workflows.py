from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEcoSphereWorkflows(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.department = cls.env["hr.department"].create({"name": "Test ESG Department"})
        cls.employee = cls.env["hr.employee"].create({"name": "Eco Tester", "department_id": cls.department.id})
        cls.factor = cls.env["ecosphere.emission.factor"].create({
            "name": "Test electricity",
            "activity_type": "electricity",
            "scope": "scope2",
            "factor_value": 0.5,
            "input_unit": "kWh",
            "output_unit": "kgCO2e",
        })

    def test_carbon_calculation_and_duplicate_prevention(self):
        source = self.env["ecosphere.environmental.goal"].create({
            "name": "Source Goal",
            "department_id": self.department.id,
            "metric": "co2e",
            "baseline_value": 100,
            "target_value": 80,
            "start_date": fields.Date.today(),
            "end_date": fields.Date.today(),
        })
        carbon = self.env["ecosphere.carbon.transaction"].create_from_source(
            source, self.factor, 10, department=self.department, employee=self.employee, module="test"
        )
        self.assertEqual(carbon.co2e_value, 5)
        again = self.env["ecosphere.carbon.transaction"].create_from_source(
            source, self.factor, 12, department=self.department, employee=self.employee, module="test"
        )
        self.assertEqual(carbon.id, again.id)
        self.assertEqual(again.activity_quantity, 12)

    def test_evidence_enforcement_and_xp_once(self):
        activity = self.env["ecosphere.csr.activity"].create({
            "name": "Test CSR",
            "start_date": fields.Datetime.now(),
            "end_date": fields.Datetime.now(),
            "evidence_required": True,
            "points": 15,
        })
        participation = self.env["ecosphere.csr.participation"].create({
            "activity_id": activity.id,
            "employee_id": self.employee.id,
        })
        with self.assertRaises(UserError):
            participation.action_approve()
        participation.proof_attachment = b"proof"
        participation.action_approve()
        participation.action_approve()
        self.assertEqual(participation.points_awarded, 15)
        self.assertEqual(
            self.env["ecosphere.points.transaction"].search_count([
                ("employee_id", "=", self.employee.id),
                ("source_model", "=", "ecosphere.csr.participation"),
                ("source_record_id", "=", participation.id),
            ]),
            1,
        )

    def test_badge_auto_award(self):
        badge = self.env["ecosphere.badge"].create({
            "name": "Test XP Badge",
            "metric": "xp",
            "operator": ">=",
            "threshold": 10,
        })
        self.env["ecosphere.points.transaction"].create({
            "employee_id": self.employee.id,
            "points": 10,
            "reason": "Test points",
        })
        self.assertTrue(self.env["ecosphere.employee.badge"].search([
            ("employee_id", "=", self.employee.id),
            ("badge_id", "=", badge.id),
        ]))

    def test_reward_balance_and_stock(self):
        reward = self.env["ecosphere.reward"].create({"name": "Test Reward", "points_required": 8, "available_stock": 1})
        self.env["ecosphere.points.transaction"].create({
            "employee_id": self.employee.id,
            "points": 10,
            "reason": "Reward balance",
        })
        redemption = self.env["ecosphere.reward.redemption"].create({
            "employee_id": self.employee.id,
            "reward_id": reward.id,
        })
        redemption.action_approve()
        self.assertEqual(reward.available_stock, 0)
        self.assertEqual(self.employee.ecosphere_points_balance, 2)
        redemption.action_cancel()
        self.assertEqual(reward.available_stock, 1)
        self.assertEqual(self.employee.ecosphere_points_balance, 10)

    def test_policy_acknowledgement_and_overdue_compliance(self):
        policy = self.env["ecosphere.esg.policy"].create({
            "name": "Test Policy",
            "policy_code": "TST-001",
            "version": "1.0",
        })
        ack = self.env["ecosphere.policy.acknowledgement"].create_if_missing(policy, self.employee)
        duplicate = self.env["ecosphere.policy.acknowledgement"].create_if_missing(policy, self.employee)
        self.assertEqual(ack.id, duplicate.id)
        ack.action_acknowledge()
        self.assertEqual(ack.status, "acknowledged")
        issue = self.env["ecosphere.compliance.issue"].create({
            "name": "Late issue",
            "department_id": self.department.id,
            "severity": "critical",
            "owner_id": self.env.user.id,
            "due_date": "2020-01-01",
        })
        self.assertTrue(issue.is_overdue)
        with self.assertRaises(ValidationError):
            self.env["res.config.settings"].create({
                "ecosphere_environmental_weight": 50,
                "ecosphere_social_weight": 30,
                "ecosphere_governance_weight": 30,
            })

    def test_score_calculation(self):
        score = self.env["ecosphere.department.score"].calculate_department_score(self.department, "2099-01")
        self.assertGreaterEqual(score.total_score, 0)
        self.assertLessEqual(score.total_score, 100)
