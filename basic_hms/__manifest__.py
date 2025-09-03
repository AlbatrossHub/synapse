# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{

    "name": "SYNAPSE",
    "version": "18.0",
    "currency": 'INR',
    "summary": "Apps basic Hospital Management system Healthcare Management Clinic Management apps manage clinic manage Patient hospital manage Healthcare system Patient Management Hospital Management Healthcare Management Clinic Management hospital Lab Test Request",
    "category": "Industry",
    "description": """
    BrowseInfo developed a new odoo/OpenERP module apps
    This module is used to manage Hospital and Healthcare Management and Clinic Management apps. 
    manage clinic manage Patient hospital in odoo manage Healthcare system Patient Management, 
    Odoo Hospital Management odoo Healthcare Management Odoo Clinic Management
    Odoo hospital Patients
    Odoo Healthcare Patients Card Report
    Odoo Healthcare Patients Medication History Report
    Odoo Healthcare Appointments
    Odoo hospital Appointments Invoice
    Odoo Healthcare Families Prescriptions Healthcare Prescriptions
    Odoo Healthcare Create Invoice from Prescriptions odoo hospital Prescription Report
    Odoo Healthcare Patient Hospitalization
    odoo Hospital Management System
    Odoo Healthcare Management System
    Odoo Clinic Management System
    Odoo Appointment Management System
    health care management system
    Generate Report for patient details, appointment, prescriptions, lab-test

    Odoo Lab Test Request and Result
    Odoo Patient Hospitalization details
    Generate Patient's Prescriptions

    
""",

    "depends": ["base", "sale_management", "stock", "account"],
    "data": [
        'security/hospital_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/product_data.xml',
        'data/doctor_recrods.xml',
        'data/therapy_type_data.xml',
        'views/login_page.xml',
        'views/main_menu_file.xml',
        'wizard/medical_appointments_invoice_wizard.xml',
        'wizard/medical_appointments_therapy_invoice_wizard.xml',
        'views/medical_appointment.xml',
        'views/therapy_type.xml',
        'views/medical_patient_medication.xml',
        'views/medical_patient.xml',
        'views/medical_physician.xml',
        'views/medical_vaccination.xml',
        'views/res_partner.xml',
        'views/medical_insurance_plan.xml',
        'report/report_view.xml',
        'report/appointment_recipts_report_template.xml',
        'report/patient_card_report.xml',
    ],
    "assets": {
        "web.assets_frontend": [
            "basic_hms/static/src/css/style.css",
        ],
    },
    "author": "BROWSEINFO",
    'website': "https://www.browseinfo.com/demo-request?app=basic_hms&version=18&edition=Community",
    "installable": True,
    "application": True,
    "auto_install": False,
    "images": ["static/description/Banner.gif"],
    'live_test_url': 'https://www.browseinfo.com/demo-request?app=basic_hms&version=18&edition=Community',
    "license":'OPL-1',

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
