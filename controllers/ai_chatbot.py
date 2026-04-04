import json

from odoo import http
from odoo.http import request


class BaladiyaChatbot(http.Controller):

    @http.route('/baladiya/chatbot/message', type='json', auth='public', csrf=False)
    def chatbot_message(self, message='', history=None):
        ai_service = request.env['baladiya.ai.service'].sudo()
        response = ai_service.ai_chatbot_respond(message, history)
        return {'response': response}

    @http.route('/baladiya/ai-dashboard', type='http', auth='user', website=True)
    def ai_dashboard(self, **kw):
        # Read cached predictions
        data_str = request.env['ir.config_parameter'].sudo().get_param(
            'baladiya.ai_dashboard_data', '{}')
        date_str = request.env['ir.config_parameter'].sudo().get_param(
            'baladiya.ai_dashboard_date', '')
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            data = {}

        # Get active request stats
        Request = request.env['baladiya.service.request'].sudo()
        total_active = Request.search_count([
            ('state', 'not in', ('done', 'rejected', 'cancelled'))])
        total_overdue = Request.search_count([('sla_status', '=', 'overdue')])
        total_completed = Request.search_count([('state', '=', 'done')])

        return request.render('baladiya.ai_dashboard_template', {
            'data': data,
            'date_str': date_str,
            'total_active': total_active,
            'total_overdue': total_overdue,
            'total_completed': total_completed,
            'page_name': 'ai_dashboard',
        })

    @http.route('/baladiya/ai-dashboard/refresh', type='http', auth='user', website=True)
    def ai_dashboard_refresh(self, **kw):
        request.env['baladiya.service.request'].sudo().action_open_ai_dashboard()
        return request.redirect('/baladiya/ai-dashboard')
