from odoo import api, fields, models, _


class BaladiyaServiceCategory(models.Model):
    _name = 'baladiya.service.category'
    _description = 'Service Category'
    _order = 'name'

    name = fields.Char(string='Service Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True)
    department_id = fields.Many2one(
        'baladiya.department', string='Department', required=True, ondelete='restrict')
    icon = fields.Char(
        string='Icon Class', default='fa fa-file-text-o',
        help='FontAwesome icon class, e.g. fa fa-building')
    fee_amount = fields.Float(string='Service Fee (AED)', digits=(16, 2))
    requires_inspection = fields.Boolean(string='Requires Inspection', default=False)
    estimated_days = fields.Integer(string='Estimated Processing Days', default=7)
    required_documents = fields.Text(
        string='Required Documents', help='List of documents the citizen must attach')
    description = fields.Html(string='Description')
    active = fields.Boolean(default=True)
    color = fields.Integer(string='Color Index')

    request_count = fields.Integer(string='Requests', compute='_compute_request_count')

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Service category code must be unique!',
    )

    def _compute_request_count(self):
        for cat in self:
            cat.request_count = self.env['baladiya.service.request'].search_count(
                [('category_id', '=', cat.id)])

    def action_view_requests(self):
        self.ensure_one()
        return {
            'name': _('Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'baladiya.service.request',
            'view_mode': 'list,form',
            'domain': [('category_id', '=', self.id)],
        }
