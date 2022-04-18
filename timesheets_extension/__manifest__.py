# -*- coding: utf-8 -*-
{
    'name': "Timesheets Extension",

    'summary': """
        Module Timesheets / Time Off
        """,

    'description': """
This module implements a timesheet extension.
==========================================

    """,

    'author': "Infosquare",
    'website': "https://www.infosquaregroup.com/",
    'license': 'LGPL-3',
    'sequence': -150,

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'hr_timesheet',
                "hr_holidays",
                ],

    # always loaded
    'data': [
        'data/mail_template.xml',
        'views/timesheet.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'images': [],
    'qweb': [],

    'installable': True,
    'application': True,
    'auto_install': False,
}
