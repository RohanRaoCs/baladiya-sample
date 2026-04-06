import json

from odoo import http, fields
from odoo.http import request

DISTRICT_LABELS = {
    'al_majaz': 'Al Majaz', 'al_nahda': 'Al Nahda', 'al_qasimia': 'Al Qasimia',
    'al_khan': 'Al Khan', 'al_taawun': 'Al Taawun', 'muwaileh': 'Muwaileh',
    'al_juraina': 'Al Juraina', 'al_fisht': 'Al Fisht', 'al_mamzar': 'Al Mamzar',
    'sharqan': 'Sharqan', 'al_ramla': 'Al Ramla', 'al_yarmook': 'Al Yarmook',
    'bu_daniq': 'Bu Daniq', 'al_gharb': 'Al Gharb',
}


class BaladiyaChatbot(http.Controller):

    @http.route('/baladiya/chatbot/message', type='json', auth='public', csrf=False)
    def chatbot_message(self, message='', history=None):
        ai_service = request.env['baladiya.ai.service'].sudo()
        response = ai_service.ai_chatbot_respond(message, history)
        return {'response': response}

    @http.route('/baladiya/ai-dashboard', type='http', auth='user', website=True)
    def ai_dashboard(self, **kw):
        Req = request.env['baladiya.service.request'].sudo()
        today = fields.Date.today()
        month_start = today.replace(day=1)

        # ==================== KPI STATS ====================
        total_all = Req.search_count([])
        total_active = Req.search_count([('state', 'not in', ('done', 'rejected'))])
        total_completed = Req.search_count([('state', '=', 'done')])
        completed_month = Req.search_count([
            ('state', '=', 'done'),
            ('completion_date', '>=', month_start)])
        total_overdue = Req.search_count([('sla_status', '=', 'overdue')])
        submitted_today = Req.search_count([('submission_date', '=', today)])
        pending_review = Req.search_count([('state', '=', 'under_review')])

        # SLA Compliance: completed on time / total completed
        completed_recs = Req.search([('state', '=', 'done'), ('deadline', '!=', False)])
        on_time = len([r for r in completed_recs if r.completion_date and r.completion_date <= r.deadline])
        sla_compliance = round(on_time / len(completed_recs) * 100, 1) if completed_recs else 100.0

        # Avg processing days
        completed_with_dates = completed_recs.filtered(lambda r: r.completion_date and r.submission_date)
        if completed_with_dates:
            total_days = sum((r.completion_date - r.submission_date).days for r in completed_with_dates)
            avg_days = round(total_days / len(completed_with_dates), 1)
        else:
            avg_days = 0.0

        # ==================== DISTRICT HEATMAP ====================
        district_data = []
        all_requests = Req.search([])
        for code, label in DISTRICT_LABELS.items():
            dist_reqs = all_requests.filtered(lambda r: r.district == code)
            dist_total = len(dist_reqs)
            if dist_total == 0:
                continue
            dist_active = len(dist_reqs.filtered(lambda r: r.state not in ('done', 'rejected')))
            dist_overdue = len(dist_reqs.filtered(lambda r: r.sla_status == 'overdue'))
            dist_completed = len(dist_reqs.filtered(lambda r: r.state == 'done'))
            pct = round(dist_total / len(all_requests) * 100, 1) if all_requests else 0
            district_data.append({
                'name': label,
                'total': dist_total,
                'active': dist_active,
                'completed': dist_completed,
                'overdue': dist_overdue,
                'pct': pct,
            })
        district_data.sort(key=lambda d: d['total'], reverse=True)

        # ==================== ACTIVITY FEED ====================
        recent_requests = Req.search([], order='write_date desc', limit=15)
        activity_feed = []
        state_labels = dict(Req._fields['state'].selection)
        for r in recent_requests:
            activity_feed.append({
                'name': r.name,
                'tracking_code': r.tracking_code,
                'state': state_labels.get(r.state, r.state),
                'category': r.category_id.name,
                'department': r.department_id.name,
                'citizen': r.citizen_id.name,
                'timestamp': r.write_date.strftime('%b %d, %H:%M') if r.write_date else '',
            })

        # ==================== AI PREDICTIONS (cached) ====================
        data_str = request.env['ir.config_parameter'].sudo().get_param(
            'baladiya.ai_dashboard_data', '{}')
        date_str = request.env['ir.config_parameter'].sudo().get_param(
            'baladiya.ai_dashboard_date', '')
        try:
            ai_data = json.loads(data_str)
        except json.JSONDecodeError:
            ai_data = {}

        return request.render('baladiya.ai_dashboard_template', {
            # KPIs
            'total_all': total_all,
            'total_active': total_active,
            'total_completed': total_completed,
            'completed_month': completed_month,
            'total_overdue': total_overdue,
            'submitted_today': submitted_today,
            'pending_review': pending_review,
            'sla_compliance': sla_compliance,
            'avg_days': avg_days,
            # District
            'district_data': district_data,
            # Activity
            'activity_feed': activity_feed,
            # AI
            'data': ai_data,
            'date_str': date_str,
            'page_name': 'ai_dashboard',
        })

    @http.route('/baladiya/ai-dashboard/refresh', type='http', auth='user', website=True)
    def ai_dashboard_refresh(self, **kw):
        request.env['baladiya.service.request'].sudo().action_open_ai_dashboard()
        return request.redirect('/baladiya/ai-dashboard')
