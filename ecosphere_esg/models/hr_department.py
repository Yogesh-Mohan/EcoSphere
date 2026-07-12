# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrDepartment(models.Model):
    _inherit = "hr.department"

    code = fields.Char(
        string="Department Code",
        index=True,
        copy=False,
        help="Short ESG/reporting code used in scorecards and reports.",
    )
    esg_manager_id = fields.Many2one(
        comodel_name="hr.employee",
        string="ESG Manager",
        check_company=True,
        help="Employee responsible for department-level ESG coordination.",
    )
    esg_status = fields.Selection(
        selection=[
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("monitoring", "Monitoring"),
        ],
        string="ESG Status",
        default="active",
        required=True,
    )
    esg_employee_count = fields.Integer(
        string="Active Employees",
        compute="_compute_esg_employee_count",
    )
    environmental_score = fields.Float(
        string="Environmental Score",
        digits=(16, 2),
        readonly=True,
        help="Latest calculated environmental score for this department.",
    )
    social_score = fields.Float(
        string="Social Score",
        digits=(16, 2),
        readonly=True,
        help="Latest calculated social score for this department.",
    )
    governance_score = fields.Float(
        string="Governance Score",
        digits=(16, 2),
        readonly=True,
        help="Latest calculated governance score for this department.",
    )
    total_esg_score = fields.Float(
        string="Total ESG Score",
        digits=(16, 2),
        readonly=True,
        help="Latest weighted ESG score for this department.",
    )

    _sql_constraints = [
        (
            "code_company_uniq",
            "unique(code, company_id)",
            "The department code must be unique per company.",
        ),
    ]

    @api.depends("member_ids", "member_ids.active")
    def _compute_esg_employee_count(self):
        counts = dict.fromkeys(self.ids, 0)
        if self.ids:
            groups = self.env["hr.employee"].read_group(
                [("department_id", "in", self.ids), ("active", "=", True)],
                ["department_id"],
                ["department_id"],
            )
            counts.update({group["department_id"][0]: group["department_id_count"] for group in groups})
        for department in self:
            department.esg_employee_count = counts.get(department.id, 0)

    @api.constrains("company_id", "esg_manager_id")
    def _check_esg_manager_company(self):
        for department in self:
            manager = department.esg_manager_id
            if department.company_id and manager.company_id and manager.company_id != department.company_id:
                raise ValidationError(_("The ESG manager must belong to the same company as the department."))

    def action_view_esg_employees(self):
        self.ensure_one()
        return {
            "name": _("Department Employees"),
            "type": "ir.actions.act_window",
            "res_model": "hr.employee",
            "view_mode": "tree,form,kanban",
            "domain": [("department_id", "=", self.id)],
            "context": {"default_department_id": self.id},
        }
