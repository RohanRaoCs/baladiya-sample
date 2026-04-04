{
    'name': 'Baladiya - Smart Municipality',
    'version': '19.0.1.0.0',
    'category': 'Services',
    'summary': 'Unified Smart Municipality ERP Platform — Sharjah',
    'description': """
        Baladiya: A unified smart municipality platform where citizens submit
        service requests (building permits, road complaints, trade licenses, etc.)
        through a self-service portal, and municipal employees process them via
        Kanban workflows with SLA tracking and departmental routing.
    """,
    'author': 'Baladiya Team',
    'depends': ['base', 'mail', 'portal', 'web'],
    'data': [
        # Security
        'security/baladiya_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/baladiya_data.xml',
        'data/mail_template_data.xml',
        # Wizard
        'wizard/baladiya_reject_wizard_views.xml',
        # Views
        'views/baladiya_department_views.xml',
        'views/baladiya_service_category_views.xml',
        'views/baladiya_service_request_views.xml',
        'views/res_partner_views.xml',
        'views/baladiya_portal_templates.xml',
        'views/baladiya_menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'baladiya/static/src/css/baladiya_portal.css',
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
