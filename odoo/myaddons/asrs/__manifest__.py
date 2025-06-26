# -*- coding: utf-8 -*-
{
    'name': "Intelligent_warehouse",
    'depends': ['base','web'],
    'summary': "Warehouse management system",
    'category': 'Uncategorized',
    'version': '18.0.0.1',
    'data': [
        'security/ir.model.access.csv',
        'views/control_system_operate_views.xml',
        'views/warehouse_property_views.xml',
        'views/warehouse_information_views.xml',
        'views/warehouse_automation_views.xml',
        'views/control_system_views.xml',
        'views/frame_barcode_views.xml',
        'views/warehouse_settings_views.xml',
        'views/warehouse_menus.xml',
        # 'data/scheduled_actions.xml',
        #'views/assets.xml'
    ],
    'assets': {
        'web.assets_backend': [

            'asrs/static/src/js/refresh_base_number.js',
            'asrs/static/src/xml/refresh_base_number_template.xml',

        ]
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    # "post_init_hook": "hooks.my_post_init_hook",
    # 'uninstall_hook': None,
}
