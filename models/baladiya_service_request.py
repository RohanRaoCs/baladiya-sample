import random
import string
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


DISTRICT_SELECTION = [
    ('al_majaz', 'Al Majaz'),
    ('al_nahda', 'Al Nahda'),
    ('al_qasimia', 'Al Qasimia'),
    ('al_khan', 'Al Khan'),
    ('al_taawun', 'Al Taawun'),
    ('muwaileh', 'Muwaileh'),
    ('al_juraina', 'Al Juraina'),
    ('al_fisht', 'Al Fisht'),
    ('al_mamzar', 'Al Mamzar'),
    ('sharqan', 'Sharqan'),
    ('al_ramla', 'Al Ramla'),
    ('al_yarmook', 'Al Yarmook'),
    ('bu_daniq', 'Bu Daniq'),
    ('al_gharb', 'Al Gharb'),
]

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('under_review', 'Under Review'),
    ('in_progress', 'In Progress'),
    ('inspection', 'Inspection'),
    ('pending_approval', 'Pending Approval'),
    ('approved', 'Approved'),
    ('done', 'Completed'),
    ('rejected', 'Rejected'),
    ('cancelled', 'Cancelled'),
]


class BaladiyaServiceRequest(models.Model):
    _name = 'baladiya.service.request'
    _description = 'Municipal Service Request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'submission_date desc, id desc'
    _mail_post_access = 'read'

    # --- Identity ---
    name = fields.Char(string='Request Number', readonly=True, copy=False, default='New')
    tracking_code = fields.Char(
        string='Tracking Code', readonly=True, copy=False, index=True,
        help='Citizen-friendly tracking code for public lookup')

    # --- Parties ---
    citizen_id = fields.Many2one(
        'res.partner', string='Citizen', required=True, tracking=True,
        domain="[('is_citizen', '=', True)]")
    category_id = fields.Many2one(
        'baladiya.service.category', string='Service Category',
        required=True, tracking=True)
    department_id = fields.Many2one(
        'baladiya.department', string='Department',
        compute='_compute_department_id', store=True, readonly=True)
    officer_id = fields.Many2one('res.users', string='Assigned Officer', tracking=True)
    approver_id = fields.Many2one('res.users', string='Approved By', readonly=True)

    # --- Details ---
    description = fields.Html(string='Description')
    address = fields.Text(string='Location / Address')
    district = fields.Selection(DISTRICT_SELECTION, string='District', tracking=True)

    # --- Workflow ---
    state = fields.Selection(
        STATE_SELECTION, string='Status', default='draft',
        required=True, tracking=True, group_expand=True)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', default='0', tracking=True)

    # --- Dates ---
    submission_date = fields.Date(string='Submission Date', readonly=True)
    deadline = fields.Date(string='Deadline', compute='_compute_deadline', store=True)
    completion_date = fields.Date(string='Completion Date', readonly=True)

    # --- SLA ---
    sla_status = fields.Selection([
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('overdue', 'Overdue'),
    ], string='SLA Status', compute='_compute_sla_status', store=True)

    # --- Financial ---
    fee_amount = fields.Float(
        string='Fee Amount (AED)', compute='_compute_fee_amount',
        store=True, readonly=False, digits=(16, 2))
    fee_paid = fields.Boolean(string='Fee Paid', default=False, tracking=True)

    # --- Attachments ---
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    document_count = fields.Integer(compute='_compute_document_count')

    # --- Feedback ---
    citizen_rating = fields.Selection([
        ('1', '1 - Poor'),
        ('2', '2 - Fair'),
        ('3', '3 - Good'),
        ('4', '4 - Very Good'),
        ('5', '5 - Excellent'),
    ], string='Citizen Rating')
    citizen_feedback = fields.Text(string='Citizen Feedback')

    # --- Internal ---
    internal_notes = fields.Html(string='Internal Notes')
    rejection_reason = fields.Text(string='Rejection Reason', readonly=True)

    # ==================== COMPUTED FIELDS ====================

    @api.depends('category_id')
    def _compute_department_id(self):
        for rec in self:
            rec.department_id = rec.category_id.department_id if rec.category_id else False

    @api.depends('submission_date', 'category_id.estimated_days')
    def _compute_deadline(self):
        for rec in self:
            if rec.submission_date and rec.category_id and rec.category_id.estimated_days:
                rec.deadline = rec.submission_date + timedelta(days=rec.category_id.estimated_days)
            else:
                rec.deadline = False

    @api.depends('deadline', 'state')
    def _compute_sla_status(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.state in ('done', 'rejected', 'cancelled') or not rec.deadline:
                rec.sla_status = False
            elif today > rec.deadline:
                rec.sla_status = 'overdue'
            elif today >= rec.deadline - timedelta(days=2):
                rec.sla_status = 'at_risk'
            else:
                rec.sla_status = 'on_track'

    @api.depends('category_id.fee_amount')
    def _compute_fee_amount(self):
        for rec in self:
            if rec.category_id:
                rec.fee_amount = rec.category_id.fee_amount

    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.attachment_ids)

    def _compute_access_url(self):
        for rec in self:
            rec.access_url = '/my/requests/%s' % rec.id

    # ==================== CRUD ====================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'baladiya.service.request') or 'New'
            if not vals.get('tracking_code'):
                cat = self.env['baladiya.service.category'].browse(
                    vals.get('category_id'))
                prefix = cat.code if cat else 'SRV'
                year = fields.Date.context_today(self).year
                suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                vals['tracking_code'] = '%s-%s-%s' % (prefix, year, suffix)
        return super().create(vals_list)

    # ==================== WORKFLOW ACTIONS ====================

    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft requests can be submitted.'))
            rec.write({
                'state': 'submitted',
                'submission_date': fields.Date.context_today(self),
            })
            template = self.env.ref('baladiya.mail_template_request_submitted', raise_if_not_found=False)
            if template:
                template.send_mail(rec.id, force_send=False)

    def action_review(self):
        self.write({'state': 'under_review'})

    def action_start_progress(self):
        self.write({'state': 'in_progress'})

    def action_start_inspection(self):
        self.write({'state': 'inspection'})

    def action_request_approval(self):
        self.write({'state': 'pending_approval'})

    def action_approve(self):
        for rec in self:
            rec.write({
                'state': 'approved',
                'approver_id': self.env.uid,
            })
            template = self.env.ref('baladiya.mail_template_request_approved', raise_if_not_found=False)
            if template:
                template.send_mail(rec.id, force_send=False)

    def action_complete(self):
        for rec in self:
            rec.write({
                'state': 'done',
                'completion_date': fields.Date.context_today(self),
            })
            template = self.env.ref('baladiya.mail_template_request_completed', raise_if_not_found=False)
            if template:
                template.send_mail(rec.id, force_send=False)

    def action_reject(self):
        self.ensure_one()
        return {
            'name': _('Reject Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'baladiya.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id},
        }

    def action_cancel(self):
        for rec in self:
            if rec.state in ('done', 'cancelled'):
                raise UserError(_('Cannot cancel a completed or already cancelled request.'))
            rec.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft', 'rejection_reason': False})

    def action_view_attachments(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.attachment_ids.ids)],
        }
