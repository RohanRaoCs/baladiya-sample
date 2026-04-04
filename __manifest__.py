{
    'name': 'Baladiya - Smart Municipality',
    'version': '19.0.2.0.0',
    'category': 'Services',
    'summary': 'AI-Powered Unified Smart Municipality ERP Platform — Sharjah',
    'description': """
        Baladiya: An AI-powered smart municipality platform where citizens submit
        service requests through a self-service portal, and municipal employees
        process them via Kanban workflows with SLA tracking. Features 6 AI Brains:
        Auto-Triage, Document Validator, Response Drafter, Predictive Dashboard,
        Citizen Chatbot, and Request Summarizer.
    """,
    'author': 'Baladiya Team',
    'depends': ['base', 'mail', 'portal', 'web'],
    'data': [
        # Security
        'security/baladiya_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/baladiya_data.xml',
        'data/baladiya_ai_data.xml',
        'data/mail_template_data.xml',
        # Wizard
        'wizard/baladiya_reject_wizard_views.xml',
        'wizard/baladiya_ai_draft_wizard_views.xml',
        # Views
        'views/baladiya_department_views.xml',
        'views/baladiya_service_category_views.xml',
        'views/baladiya_service_request_views.xml',
        'views/res_partner_views.xml',
        'views/baladiya_portal_templates.xml',
        'views/baladiya_ai_chatbot_templates.xml',
        'views/baladiya_ai_dashboard_views.xml',
        'views/baladiya_menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'baladiya/static/src/css/baladiya_portal.css',
            'baladiya/static/src/css/baladiya_chatbot.css',
            'baladiya/static/src/js/baladiya_chatbot.js',
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
