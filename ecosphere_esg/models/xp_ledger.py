# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class EsgXpLedger(models.Model):
    _name = "esg.xp.ledger"
    _description = "ESG XP and Points Ledger"
    _inherit = ["mail.thread"]
    _order = "date desc, id desc"
    _check_company_auto = True

    employee_id = fields.Many2one("hr.employee", required=True, check_company=True, index=True, tracking=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True, tracking=True)
    date = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True, tracking=True)
    transaction_type = fields.Selection(
        selection=[
            ("csr_approval", "CSR Approval"),
            ("challenge_completion", "Challenge Completion"),
            ("badge_bonus", "Badge Bonus"),
            ("admin_adjustment", "Administrator Adjustment"),
            ("reward_redemption", "Reward Redemption"),
            ("reversal", "Reversal"),
        ],
        required=True,
        index=True,
        tracking=True,
    )
    xp_amount = fields.Float(string="XP Amount", digits=(16, 2), tracking=True)
    points_amount = fields.Float(string="Points Amount", digits=(16, 2), tracking=True)
    source_model = fields.Char(required=True, index=True, tracking=True)
    source_res_id = fields.Integer(required=True, index=True, tracking=True)
    description = fields.Char(required=True, tracking=True)
    reversal_of_id = fields.Many2one("esg.xp.ledger", string="Reversal Of", check_company=True, index=True, tracking=True)

    @api.constrains("employee_id", "company_id", "xp_amount", "points_amount", "reversal_of_id")
    def _check_ledger_values(self):
        for entry in self:
            if entry.employee_id.company_id and entry.employee_id.company_id != entry.company_id:
                raise ValidationError(_("The ledger employee must belong to the ledger company."))
            if not entry.xp_amount and not entry.points_amount:
                raise ValidationError(_("A ledger entry must contain XP, points, or both."))
            if entry.reversal_of_id:
                if entry.reversal_of_id.employee_id != entry.employee_id:
                    raise ValidationError(_("A reversal must use the same employee as the original entry."))
                if entry.reversal_of_id.company_id != entry.company_id:
                    raise ValidationError(_("A reversal must use the same company as the original entry."))

    def write(self, vals):
        raise UserError(_("XP ledger entries are immutable. Create a reversal entry instead."))

    def unlink(self):
        raise UserError(_("XP ledger entries are immutable. Create a reversal entry instead."))

    @api.model
    def create_entry(self, employee, transaction_type, xp_amount, points_amount, source_record, description, reversal_of=False):
        return self.create({
            "employee_id": employee.id,
            "company_id": employee.company_id.id or self.env.company.id,
            "transaction_type": transaction_type,
            "xp_amount": xp_amount,
            "points_amount": points_amount,
            "source_model": source_record._name,
            "source_res_id": source_record.id,
            "description": description,
            "reversal_of_id": reversal_of.id if reversal_of else False,
        })

    @api.model
    def balance_for_employee(self, employee):
        result = self.read_group(
            [("employee_id", "=", employee.id)],
            ["xp_amount:sum", "points_amount:sum"],
            [],
        )
        if not result:
            return {"xp": 0.0, "points": 0.0}
        return {"xp": result[0].get("xp_amount", 0.0), "points": result[0].get("points_amount", 0.0)}
