{
    'name': 'Private Products',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': 'Allows defining products visible only to specific users',
    'description': 'This module allows defining products that are only visible to specific users in the website shop.',
    'author': 'Your Name',
    'depends': ['base', 'website_sale','website'],
    'data': [
        # 'security/ir.model.access.csv',
        # 'security/private_product_security.xml',
        'views/product_template_views.xml',
        # 'views/private_product_templates.xml',
    ],
    'installable': True,
    'application': False,
}
