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

    # --- AI Brain 1: Triage ---
    ai_triage_done = fields.Boolean(default=False)
    ai_suggested_priority = fields.Selection([
        ('0', 'Normal'), ('2', 'High'), ('3', 'Urgent'),
    ], string='AI Suggested Priority')
    ai_suggested_department_id = fields.Many2one('baladiya.department', string='AI Suggested Department')
    ai_suggested_officer_id = fields.Many2one('res.users', string='AI Suggested Officer')
    ai_triage_confidence = fields.Float(string='AI Confidence %', digits=(5, 1))
    ai_triage_reasoning = fields.Text(string='AI Triage Reasoning')

    # --- AI Brain 2: Document Validation ---
    ai_doc_validation_done = fields.Boolean(default=False)
    ai_doc_completeness = fields.Float(string='Document Completeness %', digits=(5, 1))
    ai_doc_identified = fields.Text(string='AI Identified Documents')
    ai_doc_missing = fields.Text(string='AI Missing Documents')
    ai_doc_assessment = fields.Text(string='AI Document Assessment')

    # --- AI Brain 6: Insights ---
    ai_summary = fields.Char(string='AI Summary', size=250)
    ai_sentiment = fields.Selection([
        ('frustrated', 'Frustrated'),
        ('neutral', 'Neutral'),
        ('urgent', 'Urgent'),
    ], string='AI Sentiment')
    ai_patterns = fields.Text(string='AI Detected Patterns')
    ai_recommended_action = fields.Text(string='AI Recommended Action')
    ai_insights_date = fields.Datetime(string='AI Insights Generated')

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
            # AI Brain 1: Auto-triage (never blocks submission)
            try:
                rec.action_ai_triage()
            except Exception:
                pass

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

    # ==================== AI ACTIONS ====================

    def action_ai_triage(self):
        """Brain 1: AI Auto-Triage & Routing."""
        self.ensure_one()
        ai = self.env['baladiya.ai.service']
        result = ai.ai_triage_request(self)
        if result.get('error'):
            self.message_post(body=_('AI Triage failed: %s') % result['error'],
                              message_type='comment', subtype_xmlid='mail.mt_note')
            return
        # Find suggested department
        dept = False
        dept_code = result.get('suggested_department_code', '')
        if dept_code:
            dept = self.env['baladiya.department'].search([('code', '=', dept_code)], limit=1)
        self.write({
            'ai_triage_done': True,
            'ai_suggested_priority': result.get('suggested_priority', '0'),
            'ai_suggested_department_id': dept.id if dept else False,
            'ai_triage_confidence': result.get('confidence', 0),
            'ai_triage_reasoning': result.get('reasoning', ''),
        })

    def action_accept_ai_triage(self):
        """Accept AI triage suggestions."""
        self.ensure_one()
        vals = {}
        if self.ai_suggested_priority:
            vals['priority'] = self.ai_suggested_priority
        if self.ai_suggested_department_id:
            vals['department_id'] = self.ai_suggested_department_id.id
        if self.ai_suggested_officer_id:
            vals['officer_id'] = self.ai_suggested_officer_id.id
        if vals:
            self.write(vals)
            self.message_post(body=_('AI triage suggestions accepted.'),
                              message_type='comment', subtype_xmlid='mail.mt_note')

    def action_dismiss_ai_triage(self):
        """Dismiss AI triage panel."""
        self.write({'ai_triage_done': False})

    def action_ai_validate_documents(self):
        """Brain 2: AI Document Validator."""
        self.ensure_one()
        ai = self.env['baladiya.ai.service']
        result = ai.ai_validate_documents(self)
        if result.get('error'):
            raise UserError(result['error'])
        identified = result.get('identified_documents', [])
        identified_text = '\n'.join([
            '- %s → %s (%s)' % (d.get('filename', ''), d.get('likely_type', ''), d.get('matches_requirement', ''))
            for d in identified
        ]) if isinstance(identified, list) else str(identified)
        missing = result.get('missing_documents', [])
        missing_text = '\n'.join(['- %s' % m for m in missing]) if isinstance(missing, list) else str(missing)
        self.write({
            'ai_doc_validation_done': True,
            'ai_doc_completeness': result.get('completeness_score', 0),
            'ai_doc_identified': identified_text,
            'ai_doc_missing': missing_text,
            'ai_doc_assessment': result.get('assessment', ''),
        })

    def action_ai_generate_insights(self):
        """Brain 6: AI Summarizer & Insights."""
        self.ensure_one()
        ai = self.env['baladiya.ai.service']
        result = ai.ai_summarize_request(self)
        if result.get('error'):
            raise UserError(result['error'])
        self.write({
            'ai_summary': (result.get('summary', '') or '')[:250],
            'ai_sentiment': result.get('sentiment', 'neutral'),
            'ai_patterns': result.get('patterns', ''),
            'ai_recommended_action': result.get('recommended_action', ''),
            'ai_insights_date': fields.Datetime.now(),
        })

    def action_ai_draft_response(self):
        """Brain 3: Open AI Response Drafter wizard."""
        self.ensure_one()
        return {
            'name': _('AI Response Drafter'),
            'type': 'ir.actions.act_window',
            'res_model': 'baladiya.ai.draft.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id},
        }

    @api.model
    def action_open_ai_dashboard(self):
        """Brain 4: Compute AI predictions and return dashboard action."""
        ai = self.env['baladiya.ai.service']
        import json as json_mod
        try:
            result = ai.ai_predict_dashboard()
        except Exception as e:
            result = {'error': str(e)}

        # Store result for the dashboard template
        self.env['ir.config_parameter'].sudo().set_param(
            'baladiya.ai_dashboard_data', json_mod.dumps(result))
        self.env['ir.config_parameter'].sudo().set_param(
            'baladiya.ai_dashboard_date', str(fields.Datetime.now()))

        return {
            'type': 'ir.actions.act_url',
            'url': '/baladiya/ai-dashboard',
            'target': 'self',
        }
