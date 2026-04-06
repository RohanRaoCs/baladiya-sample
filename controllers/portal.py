from odoo import http, _, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class BaladiyaPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'request_count' in counters:
            partner = request.env.user.partner_id
            values['request_count'] = request.env['baladiya.service.request'].search_count(
                [('citizen_id', '=', partner.id)])
        return values

    # ==================== SERVICE CATALOG ====================

    @http.route('/my/services', type='http', auth='user', website=True)
    def portal_services_catalog(self, **kw):
        categories = request.env['baladiya.service.category'].sudo().search([])
        return request.render('baladiya.portal_services_catalog', {
            'categories': categories,
            'page_name': 'services',
        })

    # ==================== APPLICATION FORM ====================

    @http.route('/my/services/apply/<int:category_id>', type='http', auth='user', website=True)
    def portal_service_apply(self, category_id, **kw):
        category = request.env['baladiya.service.category'].sudo().browse(category_id)
        if not category.exists():
            return request.redirect('/my/services')
        partner = request.env.user.partner_id
        districts = [
            ('al_majaz', 'Al Majaz'),
            ('al_nahda', 'Al Nahda'),
            ('al_qasimia', 'Al Qasimia'),
            ('al_khan', 'Al Khan'),
            ('al_taawun', 'Al Taawun'),
            ('muwaileh', 'Muwaileh'),
            ('al_juraina', 'Al Juraina'),
            ('al_fisht', 'Al Fisht'),
            ('al_mamzar', 'Al Mamzar'),
            ('sharqan', 'Sharqan'),
            ('al_ramla', 'Al Ramla'),
            ('al_yarmook', 'Al Yarmook'),
            ('bu_daniq', 'Bu Daniq'),
            ('al_gharb', 'Al Gharb'),
        ]
        return request.render('baladiya.portal_service_apply', {
            'category': category,
            'partner': partner,
            'districts': districts,
            'page_name': 'service_apply',
        })

    @http.route('/my/services/submit', type='http', auth='user', website=True, methods=['POST'])
    def portal_service_submit(self, **post):
        partner = request.env.user.partner_id
        # Mark partner as citizen
        if not partner.is_citizen:
            partner.sudo().write({'is_citizen': True})

        category_id = int(post.get('category_id', 0))
        vals = {
            'citizen_id': partner.id,
            'category_id': category_id,
            'description': post.get('description', ''),
            'district': post.get('district', ''),
            'address': post.get('address', ''),
        }

        service_request = request.env['baladiya.service.request'].sudo().create(vals)

        # Handle file uploads
        files = request.httprequest.files.getlist('attachments')
        attachment_ids = []
        for f in files:
            if f.filename:
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': f.filename,
                    'datas': __import__('base64').b64encode(f.read()),
                    'res_model': 'baladiya.service.request',
                    'res_id': service_request.id,
                })
                attachment_ids.append(attachment.id)

        if attachment_ids:
            service_request.sudo().write({
                'attachment_ids': [(4, aid) for aid in attachment_ids]
            })

        # Auto-submit
        service_request.sudo().action_submit()

        return request.render('baladiya.portal_service_submitted', {
            'sreq': service_request,
            'page_name': 'service_submitted',
        })

    # ==================== MY REQUESTS ====================

    @http.route('/my/requests', type='http', auth='user', website=True)
    def portal_my_requests(self, **kw):
        partner = request.env.user.partner_id
        requests_list = request.env['baladiya.service.request'].sudo().search(
            [('citizen_id', '=', partner.id)], order='submission_date desc, id desc')
        return request.render('baladiya.portal_my_requests', {
            'requests': requests_list,
            'page_name': 'my_requests',
        })

    # ==================== REQUEST DETAIL ====================

    @http.route('/my/requests/<int:request_id>', type='http', auth='user', website=True)
    def portal_request_detail(self, request_id, **kw):
        partner = request.env.user.partner_id
        service_request = request.env['baladiya.service.request'].sudo().browse(request_id)
        if not service_request.exists() or service_request.citizen_id.id != partner.id:
            return request.redirect('/my/requests')

        stages = [
            ('new', 'Received'),
            ('under_review', 'AI Review'),
            ('in_progress', 'Processing'),
            ('done', 'Completed'),
        ]
        return request.render('baladiya.portal_request_detail', {
            'req': service_request,
            'stages': stages,
            'page_name': 'request_detail',
        })

    # ==================== SUBMIT FEEDBACK ====================

    @http.route('/my/requests/<int:request_id>/feedback', type='http', auth='user',
                website=True, methods=['POST'])
    def portal_submit_feedback(self, request_id, **post):
        partner = request.env.user.partner_id
        service_request = request.env['baladiya.service.request'].sudo().browse(request_id)
        if service_request.exists() and service_request.citizen_id.id == partner.id:
            service_request.write({
                'citizen_rating': post.get('rating', ''),
                'citizen_feedback': post.get('feedback', ''),
            })
        return request.redirect('/my/requests/%s' % request_id)

    # ==================== PUBLIC TRACKING ====================

    @http.route('/track', type='http', auth='public', website=True)
    def portal_track(self, **kw):
        return request.render('baladiya.portal_track', {
            'page_name': 'track',
        })

    @http.route('/track/result', type='http', auth='public', website=True)
    def portal_track_result(self, **kw):
        tracking_code = kw.get('code', '').strip().upper()
        service_request = None
        if tracking_code:
            service_request = request.env['baladiya.service.request'].sudo().search(
                [('tracking_code', '=', tracking_code)], limit=1)

        stages = [
            ('new', 'Received'),
            ('under_review', 'AI Review'),
            ('in_progress', 'Processing'),
            ('done', 'Completed'),
        ]
        return request.render('baladiya.portal_track_result', {
            'req': service_request,
            'tracking_code': tracking_code,
            'stages': stages,
            'page_name': 'track_result',
        })
