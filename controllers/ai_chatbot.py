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

        # SLA Compliance
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

        # ==================== CHART DATA ====================
        state_counts = {
            'New': Req.search_count([('state', '=', 'new')]),
            'Under Review': Req.search_count([('state', '=', 'under_review')]),
            'In Progress': Req.search_count([('state', '=', 'in_progress')]),
            'Completed': Req.search_count([('state', '=', 'done')]),
            'Rejected': Req.search_count([('state', '=', 'rejected')]),
        }

        departments = request.env['baladiya.department'].sudo().search([])
        dept_chart = {
            'labels': [d.name for d in departments],
            'values': [d.pending_count for d in departments],
        }

        # ==================== SENTIMENT BREAKDOWN ====================
        sentiment_urgent = Req.search_count([('ai_sentiment', '=', 'urgent')])
        sentiment_frustrated = Req.search_count([('ai_sentiment', '=', 'frustrated')])
        sentiment_neutral = Req.search_count([
            ('ai_sentiment', 'not in', ('urgent', 'frustrated')),
            ('ai_triage_done', '=', True),
        ])
        sentiment_total = sentiment_urgent + sentiment_frustrated + sentiment_neutral or 1

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
            'total_all': total_all,
            'total_active': total_active,
            'total_completed': total_completed,
            'completed_month': completed_month,
            'total_overdue': total_overdue,
            'submitted_today': submitted_today,
            'pending_review': pending_review,
            'sla_compliance': sla_compliance,
            'avg_days': avg_days,
            'district_data': district_data,
            'activity_feed': activity_feed,
            'state_counts_json': json.dumps(state_counts),
            'dept_chart_json': json.dumps(dept_chart),
            'sentiment_urgent': sentiment_urgent,
            'sentiment_frustrated': sentiment_frustrated,
            'sentiment_neutral': sentiment_neutral,
            'sentiment_total': sentiment_total,
            'data': ai_data,
            'date_str': date_str,
            'page_name': 'ai_dashboard',
        })

    @http.route('/baladiya/ai-dashboard/refresh', type='http', auth='user', website=True)
    def ai_dashboard_refresh(self, **kw):
        request.env['baladiya.service.request'].sudo().action_open_ai_dashboard()
        return request.redirect('/baladiya/ai-dashboard')

    @http.route('/baladiya/ai-dashboard/briefing', type='json', auth='user')
    def ai_dashboard_briefing(self, **kw):
        Req = request.env['baladiya.service.request'].sudo()
        today = fields.Date.today()
        month_start = today.replace(day=1)

        total_all = Req.search_count([])
        total_active = Req.search_count([('state', 'not in', ('done', 'rejected'))])
        completed_month = Req.search_count([('state', '=', 'done'), ('completion_date', '>=', month_start)])
        total_overdue = Req.search_count([('sla_status', '=', 'overdue')])
        submitted_today = Req.search_count([('submission_date', '=', today)])
        pending_review = Req.search_count([('state', '=', 'under_review')])

        completed_recs = Req.search([('state', '=', 'done'), ('deadline', '!=', False)])
        on_time = len([r for r in completed_recs if r.completion_date and r.completion_date <= r.deadline])
        sla_compliance = round(on_time / len(completed_recs) * 100, 1) if completed_recs else 100.0
        completed_with_dates = completed_recs.filtered(lambda r: r.completion_date and r.submission_date)
        avg_days = round(
            sum((r.completion_date - r.submission_date).days for r in completed_with_dates) / len(completed_with_dates), 1
        ) if completed_with_dates else 0

        sentiment_urgent = Req.search_count([('ai_sentiment', '=', 'urgent')])
        sentiment_frustrated = Req.search_count([('ai_sentiment', '=', 'frustrated')])
        sentiment_neutral = Req.search_count([
            ('ai_sentiment', 'not in', ('urgent', 'frustrated')),
            ('ai_triage_done', '=', True),
        ])

        all_reqs = Req.search([])
        district_totals = {}
        for r in all_reqs:
            if r.district:
                district_totals[r.district] = district_totals.get(r.district, 0) + 1
        top_districts = ', '.join([
            DISTRICT_LABELS.get(k, k)
            for k, _ in sorted(district_totals.items(), key=lambda x: -x[1])[:3]
        ])

        departments = request.env['baladiya.department'].sudo().search([])
        busiest = max(departments, key=lambda d: d.pending_count) if departments else None

        stats = {
            'today': str(today),
            'total_all': total_all,
            'total_active': total_active,
            'completed_month': completed_month,
            'total_overdue': total_overdue,
            'sla_compliance': sla_compliance,
            'avg_days': avg_days,
            'submitted_today': submitted_today,
            'pending_review': pending_review,
            'sentiment_urgent': sentiment_urgent,
            'sentiment_frustrated': sentiment_frustrated,
            'sentiment_neutral': sentiment_neutral,
            'top_districts': top_districts,
            'busiest_dept': busiest.name if busiest else 'N/A',
            'busiest_dept_count': busiest.pending_count if busiest else 0,
        }

        ai = request.env['baladiya.ai.service'].sudo()
        result = ai.ai_executive_briefing(stats)
        return {
            'briefing': result.get('briefing', result.get('error', 'Could not generate briefing.'))
        }
