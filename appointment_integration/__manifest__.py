{
    'name': 'Appointment Integration with HMS',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Simple integration between calendar events and medical appointments',
    'description': """
        Simple integration module that allows manual synchronization of calendar events 
        to medical appointments. Features:
        - Add sync flag to calendar events
        - Manual sync action on medical patients
        - Day-wise consolidation of appointments
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'calendar',
        'basic_hms',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/therapy_type_views.xml',
        'views/medical_patient_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
