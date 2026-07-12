# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class EsgCsrActivity(models.Model):
    _name = "esg.csr.activity"
    _description = "ESG CSR Activity"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_datetime desc, title"
    _check_company_auto = True

    title = fields.Char(required=True, tracking=True)
    reference = fields.Char(default="New", required=True, readonly=True, copy=False, tracking=True)
    category_id = fields.Many2one(
        "esg.category",
        domain="[('category_type', '=', 'csr_activity'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
        tracking=True,
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, required=True, index=True, tracking=True)
    department_ids = fields.Many2many(
        "hr.department",
        "esg_csr_activity_department_rel",
        "activity_id",
        "department_id",
        string="Eligible Departments",
        check_company=True,
        tracking=True,
    )
    organizer_id = fields.Many2one("hr.employee", check_company=True, tracking=True)
    description = fields.Html()
    location = fields.Char(tracking=True)
    start_datetime = fields.Datetime(required=True, tracking=True)
    end_datetime = fields.Datetime(required=True, tracking=True)
    capacity = fields.Integer(tracking=True)
    points = fields.Float(default=0.0, digits=(16, 2), tracking=True)
    status = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("published", "Published"),
            ("ongoing", "Ongoing"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    participation_ids = fields.One2many("esg.csr.participation", "activity_id", string="Participations")
    participant_count = fields.Integer(compute="_compute_participation_metrics", store=True)
    approved_participant_count = fields.Integer(compute="_compute_participation_metrics", store=True)
    total_volunteering_hours = fields.Float(compute="_compute_participation_metrics", store=True, digits=(16, 2))

    @api.depends("participation_ids", "participation_ids.state", "participation_ids.participation_hours")
    def _compute_participation_metrics(self):
        for activity in self:
            activity.participant_count = len(activity.participation_ids)
            approved = activity.participation_ids.filtered(lambda participation: participation.state == "approved")
            activity.approved_participant_count = len(approved)
            activity.total_volunteering_hours = sum(approved.mapped("participation_hours"))

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("reference", "New") == "New":
                vals["reference"] = sequence.next_by_code("esg.csr.activity") or "New"
        return super().create(vals_list)

    @api.constrains("start_datetime", "end_datetime", "capacity", "points", "company_id", "department_ids", "organizer_id")
    def _check_activity_values(self):
        for activity in self:
            if activity.end_datetime <= activity.start_datetime:
                raise ValidationError(_("CSR activity end time must be after the start time."))
            if activity.capacity < 0:
                raise ValidationError(_("Capacity cannot be negative."))
            if activity.points < 0:
                raise ValidationError(_("CSR activity points cannot be negative."))
            if activity.organizer_id.company_id and activity.organizer_id.company_id != activity.company_id:
                raise ValidationError(_("The organizer must belong to the activity company."))
            invalid_departments = activity.department_ids.filtered(lambda department: department.company_id and department.company_id != activity.company_id)
            if invalid_departments:
                raise ValidationError(_("Eligible departments must belong to the activity company."))

    def action_publish(self):
        self.write({"status": "published"})

    def action_start(self):
        self.write({"status": "ongoing"})

    def action_complete(self):
        self.write({"status": "completed"})

    def action_cancel(self):
        self.write({"status": "cancelled"})

    def action_join(self):
        employee = self.env.user.employee_id
        if not employee:
            raise UserError(_("Your user is not linked to an employee record."))
        for activity in self:
            activity._create_participation_for_employee(employee)

    def action_view_participations(self):
        self.ensure_one()
        return {
            "name": _("CSR Participation"),
            "type": "ir.actions.act_window",
            "res_model": "esg.csr.participation",
            "view_mode": "tree,form,graph,pivot",
            "domain": [("activity_id", "=", self.id)],
            "context": {"default_activity_id": self.id},
        }

    def _create_participation_for_employee(self, employee):
        self.ensure_one()
        if self.status not in ("published", "ongoing"):
            raise UserError(_("You can only join published or ongoing CSR activities."))
        if self.department_ids and employee.department_id not in self.department_ids:
            raise UserError(_("This CSR activity is not available to your department."))
        if self.capacity and self.participant_count >= self.capacity:
            raise UserError(_("This CSR activity has reached its capacity."))
        return self.env["esg.csr.participation"].create({
            "activity_id": self.id,
            "employee_id": employee.id,
        })
