from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_citizen = fields.Boolean(string='Is Citizen', default=False)
    emirates_id = fields.Char(string='Emirates ID', size=18)

    request_count = fields.Integer(string='Service Requests', compute='_compute_request_count')
    open_request_count = fields.Integer(string='Open Requests', compute='_compute_request_count')

    def _compute_request_count(self):
        Request = self.env['baladiya.service.request']
        for partner in self:
            domain = [('citizen_id', '=', partner.id)]
            partner.request_count = Request.search_count(domain)
            partner.open_request_count = Request.search_count(
                domain + [('state', 'not in', ('done', 'rejected', 'cancelled'))])

    def action_view_requests(self):
        self.ensure_one()
        return {
            'name': _('Service Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'baladiya.service.request',
            'view_mode': 'list,form',
            'domain': [('citizen_id', '=', self.id)],
        }
