# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, tools, SUPERUSER_ID, _

from odoo.http import request
from odoo.osv import expression
from odoo.addons.http_routing.models.ir_http import url_for
from odoo.addons.website_sale.models.website import Website




class Website(models.Model):
    _inherit = 'website'

    def sale_product_domain(self):
        if True:
            website_domain = self.get_current_website().website_domain()
            if not self.env.user._is_internal():
                website_domain = expression.AND([website_domain, ['&',('is_published', '=', True), '|', ('allowed_users','=', False),  ('allowed_users','in', [self.env.user.id])]])

            return expression.AND([self._product_domain(), website_domain])
        return super(Website, self).sale_product_domain()