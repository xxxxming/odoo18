# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
        'name': 'estate',
        'depends': ['base'],
        "data": [
            "security/ir.model.access.csv",
            "views/estate_property_views.xml",
            "views/estate_property_offer_views.xml",
            "views/estate_property_type_views.xml",
            "views/estate_property_tag_views.xml",
            "views/res_users_views.xml",
            "views/estate_menus.xml",
           #"data/estate_property_data.xml",
        ],
        'installable': True,
        'application': True,
        'license': 'LGPL-3',
}