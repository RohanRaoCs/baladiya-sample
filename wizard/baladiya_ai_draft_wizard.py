from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BaladiyaAIDraftWizard(models.TransientModel):
    _name = 'baladiya.ai.draft.wizard'
    _description = 'AI Response Draft Wizard'

    request_id = fields.Many2one('baladiya.service.request', string='Request', required=True)
    transition_type = fields.Selection([
        ('review_started', 'Review Started'),
        ('in_progress', 'Work Started'),
        ('inspection', 'Inspection Scheduled'),
        ('approval', 'Request Approved'),
        ('rejection', 'Request Rejected'),
        ('completion', 'Request Completed'),
        ('update', 'General Status Update'),
    ], string='Message Type', required=True, default='update')
    ai_draft_subject = fields.Char(string='Subject')
    ai_draft_body = fields.Html(string='Message Body')

    def action_generate_draft(self):
        self.ensure_one()
        ai_service = self.env['baladiya.ai.service']
        result = ai_service.ai_draft_response(self.request_id, self.transition_type)
        if result.get('error'):
            raise UserError(result['error'])
        self.write({
            'ai_draft_subject': result.get('subject', ''),
            'ai_draft_body': '<p>%s</p>' % result.get('body', '').replace('\n', '<br/>'),
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_send_message(self):
        self.ensure_one()
        if not self.ai_draft_body:
            raise UserError(_('Please generate or write a message before sending.'))
        # Post to chatter
        self.request_id.message_post(
            body=self.ai_draft_body,
            subject=self.ai_draft_subject,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
        return {'type': 'ir.actions.act_window_close'}
