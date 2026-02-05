{
    'name': 'DASII Assessment',
    'version': '1.0',
    'summary': 'Developmental Assessment Scale for Indian Infants',
    'category': 'Healthcare',
    'author': 'Antigravity',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/dasii_data.xml',
        'views/dasii_views.xml',
        'views/dasii_menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
