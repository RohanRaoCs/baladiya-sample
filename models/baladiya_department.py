from odoo import api, fields, models, _


class BaladiyaDepartment(models.Model):
    _name = 'baladiya.department'
    _description = 'Municipality Department'
    _order = 'name'

    name = fields.Char(string='Department Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True)
    manager_id = fields.Many2one('res.users', string='Department Manager')
    member_ids = fields.Many2many('res.users', string='Department Members')
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')

    request_count = fields.Integer(string='Total Requests', compute='_compute_request_stats')
    pending_count = fields.Integer(string='Pending Requests', compute='_compute_request_stats')
    avg_processing_days = fields.Float(string='Avg. Processing Days', compute='_compute_request_stats', digits=(16, 1))

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Department code must be unique!',
    )

    def _compute_request_stats(self):
        Request = self.env['baladiya.service.request']
        for dept in self:
            domain = [('department_id', '=', dept.id)]
            all_requests = Request.search(domain)
            dept.request_count = len(all_requests)
            dept.pending_count = len(all_requests.filtered(
                lambda r: r.state not in ('done', 'approved', 'rejected', 'cancelled')
            ))
            completed = all_requests.filtered(
                lambda r: r.state == 'done' and r.completion_date and r.submission_date
            )
            if completed:
                total_days = sum((r.completion_date - r.submission_date).days for r in completed)
                dept.avg_processing_days = total_days / len(completed)
            else:
                dept.avg_processing_days = 0.0

    def action_view_requests(self):
        self.ensure_one()
        return {
            'name': _('Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'baladiya.service.request',
            'view_mode': 'list,form',
            'domain': [('department_id', '=', self.id)],
        }

    def action_view_pending(self):
        self.ensure_one()
        return {
            'name': _('Pending Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'baladiya.service.request',
            'view_mode': 'list,form',
            'domain': [
                ('department_id', '=', self.id),
                ('state', 'not in', ('done', 'approved', 'rejected', 'cancelled')),
            ],
        }
