# # -*- coding: utf-8 -*-
# # Part of Odoo. See LICENSE file for full copyright and licensing details.
# from collections import defaultdict
# from itertools import product as cartesian_product
# from datetime import datetime
# from werkzeug.exceptions import Forbidden, NotFound
# from werkzeug.urls import url_decode, url_encode, url_parse
#
# from odoo.addons.website_sale.controllers.main import TableCompute
#
# from odoo import fields, http, SUPERUSER_ID, tools, _
# from odoo.fields import Command
# from odoo.http import request
# import logging
# from odoo.addons.base.models.ir_qweb_fields import nl2br
# from odoo.addons.http_routing.models.ir_http import slug
# from odoo.addons.payment import utils as payment_utils
# from odoo.addons.payment.controllers import portal as payment_portal
# from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
# from odoo.addons.website.controllers.main import QueryURL
# from odoo.addons.website.models.ir_http import sitemap_qs2dom
# from odoo.exceptions import AccessError, MissingError, ValidationError
# from odoo.addons.portal.controllers.portal import _build_url_w_params
# from odoo.addons.website.controllers import main
# from odoo.addons.website.controllers.form import WebsiteForm
# from odoo.addons.sale.controllers import portal
# from odoo.osv import expression
# from odoo.tools import lazy
# from odoo.tools.json import scriptsafe as json_scriptsafe
#
# _logger = logging.getLogger(__name__)
#
#
# class CustomProductVisibility(http.Controller):
#     @http.route([
#         '/shop/category/ozel-64',
#         '/shop/category/ozel-64/page/<int:page>',
#     ], type='http', auth="public", website=True)
#     def shop_special(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
#         add_qty = int(post.get('add_qty', 1))
#         try:
#             min_price = float(min_price)
#         except ValueError:
#             min_price = 0
#         try:
#             max_price = float(max_price)
#         except ValueError:
#             max_price = 0
#
#         Category = request.env['product.public.category']
#         category = Category.search([('id', '=', 64)], limit=1)
#         if not category or not category.can_access_from_current_website():
#             raise http.NotFound()
#
#         website = request.env['website'].get_current_website()
#         if ppg:
#             try:
#                 ppg = int(ppg)
#                 post['ppg'] = ppg
#             except ValueError:
#                 ppg = False
#         if not ppg:
#             ppg = website.shop_ppg or 20
#
#         ppr = website.shop_ppr or 4
#
#         attrib_list = request.httprequest.args.getlist('attrib')
#         attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
#         attributes_ids = {v[0] for v in attrib_values}
#         attrib_set = {v[1] for v in attrib_values}
#
#         keep = QueryURL('/shop/category/ozel-64', **self._shop_get_query_url_kwargs(category.id, search, min_price, max_price, **post))
#
#         now = datetime.timestamp(datetime.now())
#         pricelist = request.env['product.pricelist'].browse(request.session.get('website_sale_current_pl'))
#         if not pricelist or request.session.get('website_sale_pricelist_time', 0) < now - 60*60: # test: 1 hour in session
#             pricelist = website.get_current_pricelist()
#             request.session['website_sale_pricelist_time'] = now
#             request.session['website_sale_current_pl'] = pricelist.id
#
#         request.update_context(pricelist=pricelist.id, partner=request.env.user.partner_id)
#
#         filter_by_price_enabled = website.is_view_active('website_sale.filter_products_price')
#         if filter_by_price_enabled:
#             company_currency = website.company_id.currency_id
#             conversion_rate = request.env['res.currency']._get_conversion_rate(
#                 company_currency, pricelist.currency_id, request.website.company_id, fields.Date.today())
#         else:
#             conversion_rate = 1
#
#         url = "/shop/category/ozel-64"
#         if search:
#             post["search"] = search
#         if attrib_list:
#             post['attrib'] = attrib_list
#
#         options = self._get_search_options(
#             category=category,
#             attrib_values=attrib_values,
#             pricelist=pricelist,
#             min_price=min_price,
#             max_price=max_price,
#             conversion_rate=conversion_rate,
#             **post
#         )
#         fuzzy_search_term, product_count, search_product = self._shop_lookup_products(attrib_set, options, post, search, website)
#
#         filter_by_price_enabled = website.is_view_active('website_sale.filter_products_price')
#         if filter_by_price_enabled:
#             Product = request.env['product.template'].with_context(bin_size=True)
#             domain = self._get_search_domain(search, category, attrib_values)
#
#             from_clause, where_clause, where_params = Product._where_calc(domain).get_sql()
#             query = f"""
#                 SELECT COALESCE(MIN(list_price), 0) * {conversion_rate}, COALESCE(MAX(list_price), 0) * {conversion_rate}
#                   FROM {from_clause}
#                  WHERE {where_clause}
#             """
#             request.env.cr.execute(query, where_params)
#             available_min_price, available_max_price = request.env.cr.fetchone()
#
#             if min_price or max_price:
#                 if min_price:
#                     min_price = min_price if min_price <= available_max_price else available_min_price
#                     post['min_price'] = min_price
#                 if max_price:
#                     max_price = max_price if max_price >= available_min_price else available_max_price
#                     post['max_price'] = max_price
#
#         website_domain = website.website_domain()
#         categs_domain = [('parent_id', '=', False)] + website_domain
#         if search:
#             search_categories = Category.search(
#                 [('product_tmpl_ids', 'in', search_product.ids)] + website_domain
#             ).parents_and_self
#             categs_domain.append(('id', 'in', search_categories.ids))
#         else:
#             search_categories = Category
#         categs = lazy(lambda: Category.search(categs_domain))
#
#         if category:
#             url = "/shop/category/%s" % category.id
#
#         pager = website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
#         offset = pager['offset']
#         products = search_product[offset:offset + ppg]
#
#         ProductAttribute = request.env['product.attribute']
#         if products:
#             attributes = lazy(lambda: ProductAttribute.search([
#                 ('product_tmpl_ids', 'in', search_product.ids),
#                 ('visibility', '=', 'visible'),
#             ]))
#         else:
#             attributes = lazy(lambda: ProductAttribute.browse(attributes_ids))
#
#         layout_mode = request.session.get('website_sale_shop_layout_mode')
#         if not layout_mode:
#             if website.viewref('website_sale.products_list_view').active:
#                 layout_mode = 'list'
#             else:
#                 layout_mode = 'grid'
#             request.session['website_sale_shop_layout_mode'] = layout_mode
#
#         products_prices = lazy(lambda: products._get_sales_prices(pricelist))
#
#         values = {
#             'search': fuzzy_search_term or search,
#             'original_search': fuzzy_search_term and search,
#             'order': post.get('order', ''),
#             'category': category,
#             'attrib_values': attrib_values,
#             'attrib_set': attrib_set,
#             'pager': pager,
#             'pricelist': pricelist,
#             'add_qty': add_qty,
#             'products': products,
#             'search_product': search_product,
#             'search_count': product_count,
#             'bins': lazy(lambda: TableCompute().process(products, ppg, ppr)),
#             'ppg': ppg,
#             'ppr': ppr,
#             'categories': categs,
#             'attributes': attributes,
#             'keep': keep,
#             'search_categories_ids': search_categories.ids,
#             'layout_mode': layout_mode,
#             'products_prices': products_prices,
#             'get_product_prices': lambda product: lazy(lambda: products_prices[product.id]),
#             'float_round': tools.float_round,
#         }
#         if filter_by_price_enabled:
#             values['min_price'] = min_price or available_min_price
#             values['max_price'] = max_price or available_max_price
#             values['available_min_price'] = tools.float_round(available_min_price, 2)
#             values['available_max_price'] = tools.float_round(available_max_price, 2)
#         if category:
#             values['main_object'] = category
#         values.update(self._get_additional_shop_values(values))
#
#         user = request.env.user
#         # Filter products based on allowed_users field
#         allowed_products = products.filtered(lambda p: not p.allowed_users or user in p.allowed_users)
#
#         values['products'] = allowed_products
#         values['bins'] = lazy(lambda: TableCompute().process(allowed_products, ppg, ppr))
#
#         return request.render("website_sale.products", values)
#
#     def _get_search_options(self, category=None, attrib_values=None, pricelist=None, min_price=0.0, max_price=0.0, conversion_rate=1, **post):
#         return {
#             'displayDescription': True,
#             'displayDetail': True,
#             'displayExtraDetail': True,
#             'displayExtraLink': True,
#             'displayImage': True,
#             'allowFuzzy': not post.get('noFuzzy'),
#             'category': str(category.id) if category else None,
#             'min_price': min_price / conversion_rate,
#             'max_price': max_price / conversion_rate,
#             'attrib_values': attrib_values,
#             'display_currency': pricelist.currency_id,
#         }
#
#     def _shop_lookup_products(self, attrib_set, options, post, search, website):
#         product_count, details, fuzzy_search_term = website._search_with_fuzzy("products_only", search, limit=None, order=self._get_search_order(post), options=options)
#         search_result = details[0].get('results', request.env['product.template']).with_context(bin_size=True)
#         if attrib_set:
#             attribute_values = request.env['product.attribute.value'].browse(attrib_set)
#             values_per_attribute = defaultdict(lambda: request.env['product.attribute.value'])
#             multi_value_attribute = False
#             for value in attribute_values:
#                 values_per_attribute[value.attribute_id] |= value
#                 if len(values_per_attribute[value.attribute_id]) > 1:
#                     multi_value_attribute = True
#
#             def filter_template(template, attribute_values_list):
#                 attribute_value_to_ptav = dict()
#                 for ptav in template.attribute_line_ids.product_template_value_ids:
#                     attribute_value_to_ptav[ptav.product_attribute_value_id] = ptav.id
#                 possible_combinations = False
#                 for attribute_values in attribute_values_list:
#                     ptavs = request.env['product.template.attribute.value'].browse(
#                         [attribute_value_to_ptav[val] for val in attribute_values if val in attribute_value_to_ptav]
#                     )
#                     if len(ptavs) < len(attribute_values):
#                         continue
#                     if len(ptavs) == len(template.attribute_line_ids):
#                         if template._is_combination_possible(ptavs):
#                             return True
#                     elif len(ptavs) < len(template.attribute_line_ids):
#                         if len(attribute_values_list) == 1:
#                             if any(template._get_possible_combinations(necessary_values=ptavs)):
#                                 return True
#                         if not possible_combinations:
#                             possible_combinations = template._get_possible_combinations()
#                         if any(len(ptavs & combination) == len(ptavs) for combination in possible_combinations):
#                             return True
#                 return False
#
#             if not multi_value_attribute:
#                 possible_attrib_values_list = [attribute_values]
#             else:
#                 possible_attrib_values_list = [request.env['product.attribute.value'].browse([v.id for v in values]) for values in cartesian_product(*values_per_attribute.values())]
#
#             search_result = search_result.filtered(lambda tmpl: filter_template(tmpl, possible_attrib_values_list))
#         return fuzzy_search_term, product_count, search_result
#
#     def _shop_get_query_url_kwargs(self, category, search, min_price, max_price, attrib=None, order=None, **post):
#         return {
#             'category': category,
#             'search': search,
#             'attrib': attrib,
#             'min_price': min_price,
#             'max_price': max_price,
#             'order': order,
#         }
#
#     def _get_additional_shop_values(self, values):
#         return {}
#
#     def _get_search_domain(self, search, category, attrib_values, search_in_description=True):
#         domains = [request.website.sale_product_domain()]
#         if search:
#             for srch in search.split(" "):
#                 subdomains = [
#                     [('name', 'ilike', srch)],
#                     [('product_variant_ids.default_code', 'ilike', srch)]
#                 ]
#                 if search_in_description:
#                     subdomains.append([('website_description', 'ilike', srch)])
#                     subdomains.append([('description_sale', 'ilike', srch)])
#                 domains.append(expression.OR(subdomains))
#
#         if category:
#             domains.append([('public_categ_ids', 'child_of', int(category))])
#
#         if attrib_values:
#             attrib = None
#             ids = []
#             for value in attrib_values:
#                 if not attrib:
#                     attrib = value[0]
#                     ids.append(value[1])
#                 elif value[0] == attrib:
#                     ids.append(value[1])
#                 else:
#                     domains.append([('attribute_line_ids.value_ids', 'in', ids)])
#                     attrib = value[0]
#                     ids = [value[1]]
#             if attrib:
#                 domains.append([('attribute_line_ids.value_ids', 'in', ids)])
#
#         return expression.AND(domains)
#
#     def _get_search_order(self, post):
#         order = post.get('order') or request.env['website'].get_current_website().shop_default_sort
#         return 'is_published desc, %s, id desc' % order
