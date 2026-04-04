from odoo import fields, models, _
from odoo.exceptions import UserError


class BaladiyaRejectWizard(models.TransientModel):
    _name = 'baladiya.reject.wizard'
    _description = 'Reject Service Request Wizard'

    request_id = fields.Many2one('baladiya.service.request', string='Request', required=True)
    reason = fields.Text(string='Rejection Reason', required=True)

    def action_confirm_reject(self):
        self.ensure_one()
        if not self.reason:
            raise UserError(_('Please provide a rejection reason.'))
        self.request_id.write({
            'state': 'rejected',
            'rejection_reason': self.reason,
        })
        self.request_id.message_post(
            body=_('Request rejected. Reason: %s') % self.reason,
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )
        return {'type': 'ir.actions.act_window_close'}
