from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BaladiyaAIDraftWizard(models.TransientModel):
    _name = 'baladiya.ai.draft.wizard'
    _description = 'AI Response Draft Wizard'

    request_id = fields.Many2one('baladiya.service.request', string='Request', required=True)
    transition_type = fields.Selection([
        ('update', 'General Status Update'),
        ('completion', 'Request Completed'),
        ('rejection', 'Request Rejected'),
    ], string='Message Type', required=True, default='update')
    ai_draft_subject = fields.Char(string='Subject')
    ai_draft_body = fields.Html(string='Message Body')
    rejection_reason = fields.Text(string='Rejection Reason')

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

    def action_send_and_apply(self):
        """Send the message AND apply the workflow transition."""
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

        # Apply the workflow transition
        if self.transition_type == 'completion':
            self.request_id.action_complete_direct()
        elif self.transition_type == 'rejection':
            self.request_id.action_reject_direct(reason=self.rejection_reason or '')

        return {'type': 'ir.actions.act_window_close'}
