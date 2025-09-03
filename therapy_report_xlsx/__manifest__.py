# -*- coding: utf-8 -*-
# Part of Synapse Clinic. See LICENSE file for full copyright and licensing details.

{
    "name": "Therapy Report (XLSX)",
    "version": "18.0",
    "description": "Generate an XLSX report for medical appointments with therapy data, including commission calculations.",
    "summary": "Therapy Report | Medical Appointment Report | Therapy Commission Report | XLSX Export | Medical Billing Report",
    "category": "Healthcare",
    "license": "LGPL-3",
    "author": "Synapse Clinic",
    "website": "https://www.synapseclinic.com",
    "depends": ["basic_hms", "account"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/therapy_report_wizard.xml",
    ],
    "installable": True,
    "application": False,
}
