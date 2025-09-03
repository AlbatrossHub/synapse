# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class medical_patient_rounding(models.Model):
    _name = 'medical.patient.rounding'
    _description = 'medical patient rounding'

    name = fields.Char(string='Rounding Name', required=True)
    patient_id = fields.Many2one('medical.patient', string='Patient', required=True)
    date = fields.Datetime(string='Date', required=True, default=fields.Datetime.now)
    doctor_id = fields.Many2one('medical.physician', string='Doctor')
    notes = fields.Text(string='Notes')
    vaccines_ids = fields.One2many('medical.patient.rounding.vaccine','medical_patient_rounding_vaccine_id',string='Vaccines')
    state = fields.Selection([('draft','Draft'),('done','Done')], string="Status", default='draft')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

