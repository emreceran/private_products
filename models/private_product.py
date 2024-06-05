# from odoo import models, fields
#
# class PrivateProduct(models.Model):
#     _name = 'private.product'
#     _description = 'Private Product'
#
#     name = fields.Char(string="Product Name", required=True)
#     user_ids = fields.Many2many('res.users', string="Allowed Users")
#     product_id = fields.Many2one('product.template', string="Product", required=True)
#
#
# class ProductTemplate(models.Model):
#     _inherit = 'product.template'
#
#     private_product_ids = fields.One2many('private.product', 'product_id', string="Private Products")