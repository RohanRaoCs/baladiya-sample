import json
import logging
import re

import requests as http_requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'
DEFAULT_MODEL = 'gpt-4o-mini'
DEFAULT_TIMEOUT = 30


class BaladiyaAIService(models.AbstractModel):
    _name = 'baladiya.ai.service'
    _description = 'Baladiya AI Service (OpenAI)'

    # ==================== CORE API ====================

    def _get_api_key(self):
        key = self.env['ir.config_parameter'].sudo().get_param('baladiya.openai_api_key', '')
        if not key or key == 'YOUR_API_KEY_HERE':
            raise UserError(_('OpenAI API key not configured. Go to Settings → Technical → System Parameters → baladiya.openai_api_key'))
        return key

    def _get_model(self):
        return self.env['ir.config_parameter'].sudo().get_param('baladiya.openai_model', DEFAULT_MODEL)

    def _call_openai(self, system_prompt, user_prompt, temperature=0.3, max_tokens=1000):
        api_key = self._get_api_key()
        model = self._get_model()
        headers = {
            'Authorization': 'Bearer %s' % api_key,
            'Content-Type': 'application/json',
        }
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'temperature': temperature,
            'max_tokens': max_tokens,
            'response_format': {'type': 'json_object'},
        }
        try:
            resp = http_requests.post(
                OPENAI_API_URL, json=payload, headers=headers, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            content = data['choices'][0]['message']['content']
            return json.loads(content)
        except http_requests.exceptions.Timeout:
            _logger.warning('OpenAI API timeout')
            return {'error': 'AI service timed out. Please try again.'}
        except http_requests.exceptions.RequestException as e:
            _logger.warning('OpenAI API error: %s', e)
            return {'error': 'AI service unavailable: %s' % str(e)}
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            _logger.warning('OpenAI response parse error: %s', e)
            return {'error': 'Failed to parse AI response.'}

    def _call_openai_text(self, system_prompt, user_prompt, temperature=0.5, max_tokens=1000):
        """Like _call_openai but returns plain text (no JSON mode)."""
        api_key = self._get_api_key()
        model = self._get_model()
        headers = {
            'Authorization': 'Bearer %s' % api_key,
            'Content-Type': 'application/json',
        }
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'temperature': temperature,
            'max_tokens': max_tokens,
        }
        try:
            resp = http_requests.post(
                OPENAI_API_URL, json=payload, headers=headers, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            _logger.warning('OpenAI API error: %s', e)
            return 'Sorry, I am unable to respond right now. Please try again later.'

    # ==================== HELPER ====================

    def _strip_html(self, html_text):
        if not html_text:
            return ''
        clean = re.sub(r'<[^>]+>', ' ', str(html_text))
        return re.sub(r'\s+', ' ', clean).strip()

    def _get_services_context(self):
        categories = self.env['baladiya.service.category'].sudo().search([])
        return '\n'.join([
            '- %s (Code: %s, Dept: %s, Fee: %s AED, Est. %s days, Docs: %s)' % (
                c.name, c.code, c.department_id.name, c.fee_amount,
                c.estimated_days, c.required_documents or 'None')
            for c in categories
        ])

    # ==================== BRAIN 1: TRIAGE ====================

    def ai_triage_request(self, request_rec):
        departments = self.env['baladiya.department'].sudo().search([])
        dept_info = ', '.join(['%s (%s)' % (d.name, d.code) for d in departments])

        # Find recent similar requests
        recent = self.env['baladiya.service.request'].sudo().search([
            ('district', '=', request_rec.district),
            ('submission_date', '>=', fields.Date.subtract(fields.Date.today(), days=30)),
            ('id', '!=', request_rec.id),
        ], limit=10)
        recent_summary = '\n'.join([
            '- %s: %s (%s, %s)' % (r.tracking_code, self._strip_html(r.description)[:100],
                                     r.category_id.name, r.state)
            for r in recent
        ]) or 'None'

        system = """You are an AI triage assistant for Sharjah Municipality (Baladiya). Analyze citizen service requests to assign priority and route to the correct department.

Available departments: %s

Return a JSON object with:
- "suggested_priority": "0" for Normal, "2" for High, "3" for Urgent. Use High/Urgent for: safety hazards, health risks, sewage, flooding, fire, structural danger, blocked roads, or time-sensitive legal matters.
- "suggested_department_code": the department code that best matches the request content
- "is_duplicate": true if very similar to a recent request, false otherwise
- "duplicate_reason": explanation if duplicate
- "confidence": 0-100 confidence score
- "reasoning": 2-3 sentence explanation of your analysis""" % dept_info

        description = self._strip_html(request_rec.description)
        user = """Request Description: %s
Category chosen by citizen: %s
District: %s
Address: %s
Number of attachments: %d

Recent requests in same district (last 30 days):
%s""" % (description, request_rec.category_id.name,
         dict(request_rec._fields['district'].selection).get(request_rec.district, ''),
         request_rec.address or 'Not specified',
         len(request_rec.attachment_ids),
         recent_summary)

        return self._call_openai(system, user)

    # ==================== BRAIN 2: DOCUMENT VALIDATOR ====================

    def ai_validate_documents(self, request_rec):
        required = request_rec.category_id.required_documents or 'No specific documents required'
        uploaded = '\n'.join(['- %s' % a.name for a in request_rec.attachment_ids]) or 'No files uploaded'

        system = """You are a document validation assistant for Sharjah Municipality. Check if a citizen submitted all required documents.

Return a JSON object with:
- "completeness_score": 0-100 percentage
- "identified_documents": list of {"filename": "...", "likely_type": "...", "matches_requirement": "..."}
- "missing_documents": list of document names not found in uploads
- "assessment": brief assessment for the officer (2-3 sentences)"""

        user = """Required documents for %s:
%s

Uploaded files:
%s""" % (request_rec.category_id.name, required, uploaded)

        return self._call_openai(system, user)

    # ==================== BRAIN 3: RESPONSE DRAFTER ====================

    def ai_draft_response(self, request_rec, transition_type):
        system = """You are a professional communication assistant for Sharjah Municipality (Baladiya). Draft a polite, clear message to a citizen about their service request. Use a formal but warm tone appropriate for UAE government communication.

Return a JSON object with:
- "subject": email subject line (concise)
- "body": message body (3-5 sentences, plain text)"""

        context_map = {
            'review_started': 'The request has been received and is now under review by our team.',
            'in_progress': 'Work has begun on processing this request.',
            'inspection': 'A site inspection has been scheduled for this request.',
            'approval': 'The request has been approved by the department manager.',
            'rejection': 'The request has been reviewed but cannot be approved. Reason: %s' % (request_rec.rejection_reason or 'Not specified'),
            'completion': 'The request has been fully processed and completed.',
            'update': 'Providing a general status update on the request.',
        }

        user = """Transition: %s
Context: %s
Citizen name: %s
Request number: %s
Service: %s
Tracking code: %s
Department: %s
District: %s""" % (
            transition_type,
            context_map.get(transition_type, ''),
            request_rec.citizen_id.name,
            request_rec.name,
            request_rec.category_id.name,
            request_rec.tracking_code,
            request_rec.department_id.name,
            dict(request_rec._fields['district'].selection).get(request_rec.district, ''),
        )

        return self._call_openai(system, user)

    # ==================== BRAIN 4: PREDICTIVE DASHBOARD ====================

    def ai_predict_dashboard(self):
        active_requests = self.env['baladiya.service.request'].sudo().search([
            ('state', 'not in', ('done', 'rejected', 'cancelled')),
        ])
        departments = self.env['baladiya.department'].sudo().search([])

        requests_data = []
        for r in active_requests:
            requests_data.append({
                'id': r.id,
                'name': r.name,
                'department': r.department_id.name,
                'state': r.state,
                'submission_date': str(r.submission_date) if r.submission_date else None,
                'deadline': str(r.deadline) if r.deadline else None,
                'sla_status': r.sla_status,
                'priority': r.priority,
                'district': dict(r._fields['district'].selection).get(r.district, ''),
            })

        dept_data = []
        for d in departments:
            dept_data.append({
                'name': d.name,
                'code': d.code,
                'request_count': d.request_count,
                'pending_count': d.pending_count,
                'avg_processing_days': d.avg_processing_days,
            })

        system = """You are an operations analytics AI for Sharjah Municipality. Analyze current workload data and provide predictions.

Today's date: %s

Return a JSON object with:
- "sla_risk_requests": list of {"id": int, "name": str, "reason": str} for requests likely to miss SLA
- "busiest_department": {"name": str, "reason": str}
- "bottleneck_department": {"name": str, "reason": str, "suggestion": str}
- "recommendations": list of 3-5 actionable recommendations (strings)
- "overall_health": "good", "warning", or "critical" """ % str(fields.Date.today())

        user = """Active Requests (%d total):
%s

Department Performance:
%s""" % (len(requests_data), json.dumps(requests_data, indent=2), json.dumps(dept_data, indent=2))

        return self._call_openai(system, user, max_tokens=1500)

    # ==================== BRAIN 5: CHATBOT ====================

    def ai_chatbot_respond(self, user_message, conversation_history=None):
        services_ctx = self._get_services_context()

        # Detect tracking codes in message
        tracking_ctx = ''
        code_match = re.search(r'[A-Z]{2,4}-\d{4}-[A-Z0-9]{4}', user_message.upper())
        if code_match:
            code = code_match.group()
            req = self.env['baladiya.service.request'].sudo().search(
                [('tracking_code', '=', code)], limit=1)
            if req:
                tracking_ctx = """
Tracking code %s found! Request details:
- Request: %s
- Service: %s
- Department: %s
- Status: %s
- Submitted: %s
- Deadline: %s
- SLA: %s""" % (code, req.name, req.category_id.name, req.department_id.name,
                dict(req._fields['state'].selection).get(req.state),
                req.submission_date or 'N/A', req.deadline or 'N/A',
                req.sla_status or 'N/A')
            else:
                tracking_ctx = "\nTracking code %s was not found in our system." % code

        system = """You are a helpful assistant for Sharjah Municipality (Baladiya) citizen portal. Help citizens with:
1. Finding the right municipal service
2. Tracking request status (if they provide a tracking code like BLD-2026-A7X9)
3. Answering questions about required documents, fees, and processing times
4. Guiding through the application process

Available services:
%s

Rules:
- Be polite, concise, and helpful (2-4 sentences max)
- Only use the data provided — never make up information
- You CANNOT modify any data or submit requests
- If you can't help, direct them to visit the municipality office
- Respond in the same language the citizen uses
%s""" % (services_ctx, tracking_ctx)

        # Build messages with history
        messages = [{'role': 'system', 'content': system}]
        if conversation_history:
            for msg in conversation_history[-10:]:
                messages.append(msg)
        messages.append({'role': 'user', 'content': user_message})

        # Use text mode for chatbot (not JSON)
        api_key = self._get_api_key()
        model = self._get_model()
        headers = {
            'Authorization': 'Bearer %s' % api_key,
            'Content-Type': 'application/json',
        }
        payload = {
            'model': model,
            'messages': messages,
            'temperature': 0.5,
            'max_tokens': 500,
        }
        try:
            resp = http_requests.post(
                OPENAI_API_URL, json=payload, headers=headers, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            _logger.warning('Chatbot API error: %s', e)
            return 'Sorry, I am unable to respond right now. Please try again later or visit the municipality office for assistance.'

    # ==================== BRAIN 6: SUMMARIZER ====================

    def ai_summarize_request(self, request_rec):
        # Find similar requests in same district
        similar = self.env['baladiya.service.request'].sudo().search([
            ('district', '=', request_rec.district),
            ('category_id', '=', request_rec.category_id.id),
            ('id', '!=', request_rec.id),
            ('submission_date', '>=', fields.Date.subtract(fields.Date.today(), days=60)),
        ], limit=10)
        similar_summary = '\n'.join([
            '- %s: %s (%s)' % (s.tracking_code, self._strip_html(s.description)[:80], s.state)
            for s in similar
        ]) or 'None found'

        system = """You are an analytical AI for Sharjah Municipality officers. Analyze service requests and provide insights.

Return a JSON object with:
- "summary": one-line executive summary (max 150 characters)
- "sentiment": exactly one of "frustrated", "neutral", or "urgent"
- "patterns": notable patterns or trends (1-2 sentences). Reference similar requests if relevant.
- "recommended_action": specific next step recommendation for the officer (1-2 sentences)"""

        description = self._strip_html(request_rec.description)
        user = """Request: %s (%s)
Service: %s
Department: %s
District: %s
Description: %s
State: %s
Submitted: %s
Deadline: %s
SLA Status: %s
Priority: %s
Documents: %d attached

Similar requests in same district (last 60 days):
%s""" % (
            request_rec.name, request_rec.tracking_code,
            request_rec.category_id.name, request_rec.department_id.name,
            dict(request_rec._fields['district'].selection).get(request_rec.district, ''),
            description,
            dict(request_rec._fields['state'].selection).get(request_rec.state, ''),
            request_rec.submission_date or 'N/A',
            request_rec.deadline or 'N/A',
            request_rec.sla_status or 'N/A',
            dict(request_rec._fields['priority'].selection).get(request_rec.priority, ''),
            len(request_rec.attachment_ids),
            similar_summary,
        )

        return self._call_openai(system, user)
