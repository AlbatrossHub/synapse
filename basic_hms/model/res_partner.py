# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class res_partner(models.Model):
    _inherit = 'res.partner'
 
    relationship = fields.Char(string='Relationship')
    relative_partner_id = fields.Many2one('res.partner',string="Relative_id")
    is_patient = fields.Boolean(string='Patient')
    is_person = fields.Boolean(string="Person")
    is_doctor = fields.Boolean(string="Doctor")
    is_insurance_company = fields.Boolean(string='Insurance Company')
    is_pharmacy = fields.Boolean(string="Pharmacy")
    # Removed patient_insurance_ids - model deleted
    is_institution = fields.Boolean('Institution')
    # Removed company_insurance_ids - model deleted
    reference = fields.Char('ID Number')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: