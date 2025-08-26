# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import date,datetime, timedelta

class medical_inpatient_registration(models.Model):
    _name = 'medical.inpatient.registration'
    _description = 'IPD Registration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Registration Code", copy=False, readonly=True, index=True)
    patient_id = fields.Many2one('medical.patient',string="Patient",required=True, tracking=True)
    hospitalization_date = fields.Datetime(string="DOA",required=True, tracking=True)
    discharge_date = fields.Datetime(string="DOD", tracking=True)
    attending_physician_id = fields.Many2one('medical.physician',string="Attending Doctor", default=lambda self: self._default_doctor_id(), tracking=True)
    operating_physician_id = fields.Many2one('medical.physician',string="Operating Physician")
    admission_type = fields.Selection([('routine','Routine'),('maternity','Maternity'),('elective','Elective'),('urgent','Urgent'),('emergency','Emergency')],required=True,string="Admission Type", default="routine", tracking=True)
    medical_pathology_id = fields.Many2one('medical.pathology',string="Reason for Admission")
    info = fields.Text(string="Extra Info")
    bed_transfers_ids = fields.One2many('bed.transfer','inpatient_id',string='Transfer Bed')
    medical_diet_belief_id = fields.Many2one('medical.diet.belief',string='Belief')
    therapeutic_diets_ids = fields.One2many('medical.inpatient.diet','medical_inpatient_registration_id',string='Therapeutic_diets')
    diet_vegetarian = fields.Selection([('none','None'),('vegetarian','Vegetarian'),('lacto','Lacto Vegetarian'),('lactoovo','Lacto-Ovo-Vegetarian'),('pescetarian','Pescetarian'),('vegan','Vegan')],string="Vegetarian")
    nutrition_notes = fields.Text(string="Nutrition notes / Directions")
    state = fields.Selection([('new','New'),('confirmed','Confirmed'),('ongoingstay','On-Going Stay'),('cancel','Cancel'),('done','Done')],string="State",default="new", tracking=True)
    diet_plan = fields.Text(string="Diet Plan")
    discharge_plan = fields.Text(string="Discharge Plan")
    icu = fields.Boolean(string="ICU")
    medication_ids = fields.One2many('medical.inpatient.medication','medical_inpatient_registration_id',string='Medication')
    allday = fields.Boolean('All Day', default=False)
    duration = fields.Float('Duration', compute='_compute_duration', store=True, readonly=False)
    room_category_id = fields.Many2one("product.template", string="Room Category", required=True, domain=[("is_room", "=", True)])
    invoiced = fields.Boolean(string="Invoiced", compute="_compute_invoiced", store=True)
    invoice_id = fields.Many2one("account.move", string="Invoice")

    @api.depends('invoice_id')
    def _compute_invoiced(self):
        """ Compute invoiced field based on whether invoice_id is set. """
        for record in self:
            record.invoiced = bool(record.invoice_id)

    @api.depends('discharge_date', 'hospitalization_date')
    def _compute_duration(self):
        for event in self:
            event.duration = self._get_duration(event.hospitalization_date, event.discharge_date)

    def _get_duration(self, start, stop):
        """ Get the duration in **days** instead of hours. """
        if not start or not stop:
            return 0
        duration = (stop - start).total_seconds() / 86400  # Convert seconds to days
        return round(duration, 2)  # Keep 2 decimal places

    @api.depends('hospitalization_date', 'duration')
    def _compute_stop(self):
        """ Compute stop datetime based on duration (now in days). """
        duration_field = self._fields['duration']
        self.env.remove_to_compute(duration_field, self)
        for event in self:
            if event.hospitalization_date:
                event.discharge_date = event.hospitalization_date + timedelta(days=round(event.duration or 1.0))
                if event.allday:
                    event.discharge_date -= timedelta(seconds=1)

    @api.model
    def _default_doctor_id(self):
        return self.env.ref('basic_hms.medical_physician_1', raise_if_not_found=False) or self.env['medical.physician'].search([], limit=1)

    @api.model_create_multi
    def create(self, vals_list):
        today_str = datetime.today().strftime("%d%m%y")
        for vals in vals_list:
            apt_id = self.env['ir.sequence' ].next_by_code('medical.inpatient.registration' ) or 'IPD'
            vals['name'] = f"IPD{today_str}{apt_id}"
        return super(medical_inpatient_registration, self).create(vals_list)

    @api.model
    def default_get(self, fields):
        result = super(medical_inpatient_registration, self).default_get(fields)
        patient_id  = self.env['ir.sequence'].next_by_code('medical.inpatient.registration')
        if patient_id:
            if 'name' in fields:
                result.update({
                            'name':patient_id,
                           })
        return result

    def registration_confirm(self):
        self.write({'state': 'confirmed'})

    def registration_admission(self):
        self.write({'state': 'ongoingstay'})

    def registration_cancel(self):
        self.write({'state': 'cancel'})

    def patient_discharge(self):
        self.write({'state': 'done'})


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:s
