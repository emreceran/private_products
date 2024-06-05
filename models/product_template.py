from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    allowed_users = fields.Many2many(
        'res.users',
        'product_template_user_rel',
        'product_id',
        'user_id',
        string='Allowed Users'
    )

