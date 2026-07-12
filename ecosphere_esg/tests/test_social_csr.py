# -*- coding: utf-8 -*-

import base64

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSocialCsr(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.department = cls.env["hr.department"].create({
            "name": "CSR Test Department",
            "company_id": cls.company.id,
        })
        cls.employee = cls.env["hr.employee"].create({
            "name": "CSR Test Employee",
            "company_id": cls.company.id,
            "department_id": cls.department.id,
        })
        cls.category = cls.env["esg.category"].create({
            "name": "Community Volunteering",
            "category_type": "csr_activity",
            "company_id": cls.company.id,
        })
        cls.activity = cls.env["esg.csr.activity"].create({
            "title": "Community Cleanup",
            "category_id": cls.category.id,
            "company_id": cls.company.id,
            "department_ids": [(6, 0, [cls.department.id])],
            "start_datetime": fields.Datetime.to_string(fields.Datetime.now()),
            "end_datetime": fields.Datetime.to_string(fields.Datetime.add(fields.Datetime.now(), hours=2)),
            "points": 25.0,
            "status": "published",
        })

    def _create_attachment(self, participation):
        return self.env["ir.attachment"].create({
            "name": "csr-proof.txt",
            "datas": base64.b64encode(b"CSR proof"),
            "res_model": participation._name,
            "res_id": participation.id,
            "mimetype": "text/plain",
        })

    def test_duplicate_csr_participation_prevention(self):
        self.env["esg.csr.participation"].create({
            "activity_id": self.activity.id,
            "employee_id": self.employee.id,
        })
        with self.assertRaises(Exception):
            self.env["esg.csr.participation"].create({
                "activity_id": self.activity.id,
                "employee_id": self.employee.id,
            })

    def test_csr_evidence_requirement(self):
        participation = self.env["esg.csr.participation"].create({
            "activity_id": self.activity.id,
            "employee_id": self.employee.id,
            "participation_hours": 2.0,
            "state": "submitted",
        })
        with self.assertRaises(ValidationError):
            participation.action_approve()

    def test_csr_approval_awards_xp_once(self):
        participation = self.env["esg.csr.participation"].create({
            "activity_id": self.activity.id,
            "employee_id": self.employee.id,
            "participation_hours": 2.0,
            "state": "submitted",
        })
        attachment = self._create_attachment(participation)
        participation.proof_attachment_ids = [(4, attachment.id)]
        participation.action_approve()

        self.assertEqual(participation.state, "approved")
        self.assertEqual(participation.points_earned, 25.0)
        self.assertTrue(participation.xp_ledger_id)
        self.assertEqual(participation.xp_ledger_id.xp_amount, 25.0)
        with self.assertRaises(UserError):
            participation.action_approve()

    def test_reverse_approval_creates_reversal_ledger(self):
        participation = self.env["esg.csr.participation"].create({
            "activity_id": self.activity.id,
            "employee_id": self.employee.id,
            "participation_hours": 2.0,
            "state": "submitted",
        })
        attachment = self._create_attachment(participation)
        participation.proof_attachment_ids = [(4, attachment.id)]
        participation.action_approve()
        participation.action_reverse_approval()

        self.assertEqual(participation.state, "submitted")
        self.assertTrue(participation.reversal_ledger_id)
        self.assertEqual(participation.reversal_ledger_id.reversal_of_id, participation.xp_ledger_id)
        self.assertEqual(participation.reversal_ledger_id.points_amount, -25.0)

    def test_xp_ledger_is_immutable(self):
        entry = self.env["esg.xp.ledger"].create_entry(
            self.employee,
            "admin_adjustment",
            5.0,
            5.0,
            self.activity,
            "Test adjustment",
        )
        with self.assertRaises(UserError):
            entry.write({"points_amount": 10.0})
        with self.assertRaises(UserError):
            entry.unlink()
