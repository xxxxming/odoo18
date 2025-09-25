# -*- coding: utf-8 -*-
{
    'name': "Intelligent_warehouse",
    'depends': ['base','web'],
    'summary': "Warehouse management system",
    'category': 'Uncategorized',
    'version': '18.0.0.1',
    'data': [
        'security/ir.model.access.csv',
        'views/warehouse_system_operate_views.xml',
        'views/warehouse_property_views.xml',
        'views/warehouse_location_information_views.xml',
        'views/warehouse_automation_views.xml',
        'views/warehouse_control_system_views.xml',
        'views/warehouse_frame_barcode_views.xml',
        'views/warehouse_settings_views.xml',
        'views/warehouse_menus.xml',
        # 'data/scheduled_actions.xml',
        #'views/assets.xml'
        # 'data/warehouse_control_system_data1.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # 'asrs/static/src/js/refresh_status.js',
            # 'asrs/static/src/js/refresh_full_record.js',
            # 'asrs/static/src/js/custom_selector.js',
            'asrs/static/src/js/warehouse_bus_sync.js',

        ]
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    #'post_init_hook': 'start_plc_scheduler',
    # 'uninstall_hook': None,
}
