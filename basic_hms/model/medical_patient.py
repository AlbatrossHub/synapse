# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import date,datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class medical_patient(models.Model):
    
    _name = 'medical.patient'
    _description = 'Synapse Patient'
    _rec_name = 'patient_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    @api.depends()
    def _compute_today(self):
        for rec in self:
            rec.today = date.today()

    @api.onchange('patient_id')
    def _onchange_patient(self):
        '''
        The purpose of the method is to define a domain for the available
        purchase orders and sync patient_name.
        '''
        address_id = self.patient_id
        self.partner_address_id = address_id
        # Sync patient_name when patient_id is selected
        if self.patient_id:
            self.patient_name = self.patient_id.name

    @api.onchange('patient_name')
    def _onchange_patient_name(self):
        """Handle patient_name changes to sync with res.partner"""
        if self.patient_name:
            # If patient_id exists, update the partner name
            if self.patient_id:
                self.patient_id.name = self.patient_name
            # If no patient_id, we'll create one in the create/write method

    def print_report(self):
        return self.env.ref('basic_hms.report_print_patient_card').report_action(self)

    def action_create_new_appointment(self):
        """Create a new appointment for this patient and open the form view"""
        self.ensure_one()
        
        # Create new appointment with patient pre-selected
        appointment_vals = {
            'patient_id': self.id,
            'appointment_date': fields.Datetime.now(),
            'state': 'pending',
        }
        
        # Get default doctor if available
        if self.primary_care_physician_id:
            appointment_vals['doctor_id'] = self.primary_care_physician_id.id
        
        new_appointment = self.env['medical.appointment'].create(appointment_vals)
        
        # Return action to open the new appointment form
        return {
            'type': 'ir.actions.act_window',
            'name': f'New Appointment - {self.patient_name or self.patient_id.name}',
            'view_mode': 'form',
            'res_model': 'medical.appointment',
            'res_id': new_appointment.id,
            'target': 'current',
            'context': {
                'default_patient_id': self.id,
                'default_doctor_id': self.primary_care_physician_id.id if self.primary_care_physician_id else False,
            }
        }

    @api.depends('date_of_birth')
    def onchange_age(self):
        for rec in self:
            if rec.date_of_birth:
                d1 = rec.date_of_birth
                d2 = datetime.today().date()
                rd = relativedelta(d2, d1)
                rec.age = str(rd.years) + "y" +" "+ str(rd.months) + "m" +" "+ str(rd.days) + "d"
            else:
                rec.age = "No Date Of Birth!!"

    patient_id = fields.Many2one('res.partner',domain=[('is_patient','=',True)],string="Patient Navigation")
    patient_name = fields.Char(string='Patient Name')
    name = fields.Char(string='Id', readonly=True)
    today = fields.Date(string="Today", compute='_compute_today')
    last_name = fields.Char('Last name')
    date_of_birth = fields.Date(string="Date of Birth", tracking=True)
    sex = fields.Selection([('m', 'Male'),('f', 'Female')], string ="Gender", tracking=True)
    age = fields.Char(string="Age")
    critical_info = fields.Text(string="Patient Critical Information")
    photo = fields.Binary(string="Picture")
    blood_type = fields.Selection([('A', 'A'),('B', 'B'),('AB', 'AB'),('O', 'O')], string ="Blood Type")
    rh = fields.Selection([('-+', '+'),('--', '-')], string ="Rh")
    receivable = fields.Float(string="Receivable", readonly=True)
    # Removed current_insurance_id - model deleted
    partner_address_id = fields.Many2one('res.partner', string="Address", )
    referred_by = fields.Many2one('res.partner', string="Referred by")
    referred_by_st = fields.Char(string="Referred by")

    street = fields.Char(readonly=False, tracking=True)
    street2 = fields.Char(readonly=False, tracking=True)
    zip_code = fields.Char(readonly=False, tracking=True)
    city = fields.Char(readonly=False, tracking=True)
    state_id = fields.Many2one("res.country.state", readonly=False, tracking=True)
    country_id = fields.Many2one('res.country', readonly=False, tracking=True)
    
    primary_care_physician_id = fields.Many2one('medical.physician', string="Primary Care Doctor", tracking=True)
    patient_status = fields.Char(string="Hospitalization Status",readonly=True)
    patient_disease_ids = fields.One2many('medical.patient.disease','patient_id')
    ses = fields.Selection([
            ('None', ''),
            ('0', 'Lower'),
            ('1', 'Lower-middle'),
            ('2', 'Middle'),
            ('3', 'Middle-upper'),
            ('4', 'Higher'),
        ], 'Socioeconomics', help="SES - Socioeconomic Status", sort=False)
    notes = fields.Text(string="Extra info")
    medical_vaccination_ids = fields.One2many('medical.vaccination','medical_patient_vaccines_id')
    medical_appointments_ids = fields.One2many('medical.appointment','patient_id',string='Appointments')
    # Removed medical_ipd_ids - model deleted
    report_date = fields.Date('Date',default = datetime.today().date())
    medication_ids = fields.One2many('medical.patient.medication1','medical_patient_medication_id')
    ses_notes = fields.Text('Notes')
    mobile = fields.Char(string="Mobile", readonly=False, tracking=True)
    phone = fields.Char(string="Phone", readonly=False, tracking=True)
    email = fields.Char(string="Email", readonly=False, tracking=True)
    height = fields.Char(string="Height", tracking=True)
    weight = fields.Char(string="Weight", tracking=True)
    appointment_count = fields.Integer(string="Appointments", compute="_compute_appointment_count", default=0)

    def _compute_appointment_count(self):
        for record in self:
            record.appointment_count = self.env['medical.appointment'].search_count([('patient_id', '=', record.id)])

    def action_open_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Appointments - {self.patient_name or self.patient_id.name}',
            'view_mode': 'list,form,calendar',
            'res_model': 'medical.appointment',
            'domain': [('patient_id', '=', self.id)],
            'context': "{'create': False}",
            'search_view_id': self.env.ref('basic_hms.view_medical_appointment_search').id
        }

    def action_open_attendance_calendar(self):
        """Open patient-specific attendance calendar"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Attendance Calendar - {self.patient_name or self.patient_id.name}',
            'view_mode': 'calendar',
            'res_model': 'medical.appointment',
            'domain': [('patient_id', '=', self.id)],
            'context': "{'create': False}",
            'search_view_id': self.env.ref('basic_hms.view_medical_appointment_search').id
        }

    # Removed action_open_inpatient - model deleted
    # Removed action_open_treatments - model deleted

    def _valid_field_parameter(self, field, name):
        return name == 'sort' or super()._valid_field_parameter(field, name)

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create method to sync patient_name with res.partner
        Parent method is called first for efficiency and proper record creation
        """
        # Handle name generation and age calculation before creating records
        for val in vals_list:
            # Generate patient ID if not provided
            if not val.get('name'):
                today_str = datetime.today().strftime("%d%m%y")
                patient_id = self.env['ir.sequence'].next_by_code('medical.patient')
                if patient_id:
                    val.update({
                        'name': f"SPNIC-{patient_id}"
                    })
            
            # Calculate age if date_of_birth is provided
            if val.get('date_of_birth'):
                dt = val.get('date_of_birth')
                d1 = datetime.strptime(str(dt), "%Y-%m-%d").date()
                d2 = datetime.today().date()
                rd = relativedelta(d2, d1)
                age = str(rd.years) + "y" + " " + str(rd.months) + "m" + " " + str(rd.days) + "d"
                val.update({'age': age})
        
        # Call parent method first to create the records
        res = super(medical_patient, self).create(vals_list)
        
        # Now handle the synchronization logic for created records
        for record in res:
            # Handle patient_name synchronization with res.partner
            if record.patient_name and not record.patient_id:
                # Create new res.partner if patient_name is provided but no patient_id
                partner_vals = {
                    'name': record.patient_name,
                }
                partner_vals = self._ensure_patient_partner(partner_vals)
                # Add related fields if provided
                if record.mobile:
                    partner_vals['mobile'] = record.mobile
                if record.phone:
                    partner_vals['phone'] = record.phone
                if record.email:
                    partner_vals['email'] = record.email
                if record.street:
                    partner_vals['street'] = record.street
                if record.street2:
                    partner_vals['street2'] = record.street2
                if record.city:
                    partner_vals['city'] = record.city
                if record.state_id:
                    partner_vals['state_id'] = record.state_id.id
                if record.zip_code:
                    partner_vals['zip'] = record.zip_code
                if record.country_id:
                    partner_vals['country_id'] = record.country_id.id
                
                partner = self.env['res.partner'].create(partner_vals)
                record.patient_id = partner.id
            
            # Handle existing patient_id - sync patient_name
            elif record.patient_id and record.patient_name:
                if record.patient_id.name != record.patient_name:
                    record.patient_id.write({'name': record.patient_name})
            
            # Handle appointment context (existing logic)
            appointment = self._context.get('appointment_id')
            if appointment and record.patient_id:
                val_1 = {'name': record.patient_id.name}
                patient = self.env['res.partner'].create(val_1)
                record.patient_id = patient.id
        
        return res

    def write(self, vals):
        """
        Override write method to sync patient_name with res.partner
        Parent method is called first for efficiency and proper record updates
        """
        # Call parent method first to update the records
        res = super(medical_patient, self).write(vals)
        
        # Now handle the synchronization logic for updated records
        for record in self:
            # Sync patient_name with res.partner
            if vals.get('patient_name') and record.patient_id:
                partner_vals = {'name': vals.get('patient_name')}
                
                # Sync related fields if they are being updated
                if vals.get('mobile'):
                    partner_vals['mobile'] = vals.get('mobile')
                if vals.get('phone'):
                    partner_vals['phone'] = vals.get('phone')
                if vals.get('email'):
                    partner_vals['email'] = vals.get('email')
                if vals.get('street'):
                    partner_vals['street'] = vals.get('street')
                if vals.get('street2'):
                    partner_vals['street2'] = vals.get('street2')
                if vals.get('city'):
                    partner_vals['city'] = vals.get('city')
                if vals.get('state_id'):
                    partner_vals['state_id'] = vals.get('state_id')
                if vals.get('zip_code'):
                    partner_vals['zip'] = vals.get('zip_code')
                if vals.get('country_id'):
                    partner_vals['country_id'] = vals.get('country_id')
                
                # Update the partner
                record.patient_id.write(partner_vals)
            
            # Handle case where patient_name is updated but no patient_id exists
            elif vals.get('patient_name') and not record.patient_id:
                # Create new res.partner
                partner_vals = {
                    'name': vals.get('patient_name'),
                }
                partner_vals = self._ensure_patient_partner(partner_vals)
                # Add related fields if provided
                if vals.get('mobile'):
                    partner_vals['mobile'] = vals.get('mobile')
                if vals.get('phone'):
                    partner_vals['phone'] = vals.get('phone')
                if vals.get('email'):
                    partner_vals['email'] = vals.get('email')
                if vals.get('street'):
                    partner_vals['street'] = vals.get('street')
                if vals.get('street2'):
                    partner_vals['street2'] = vals.get('street2')
                if vals.get('city'):
                    partner_vals['city'] = vals.get('city')
                if vals.get('state_id'):
                    partner_vals['state_id'] = vals.get('state_id')
                if vals.get('zip_code'):
                    partner_vals['zip'] = vals.get('zip_code')
                if vals.get('country_id'):
                    partner_vals['country_id'] = vals.get('country_id')
                
                partner = self.env['res.partner'].create(partner_vals)
                record.patient_id = partner.id
        
        return res

    @api.constrains('date_of_death')
    def _check_date_death(self):
        for rec in self:
            if rec.date_of_birth:
                if rec.deceased == True :
                    if rec.date_of_death <= rec.date_of_birth :
                      raise UserError(_('Date Of Death Can Not Less Than Date Of Birth.' ))

    def copy(self, default=None):
        for rec in self:
            raise UserError(_('You Can Not Duplicate Patient.' ))

    @api.model
    def _ensure_patient_partner(self, partner_vals):
        """Helper method to ensure res.partner is created as a person"""
        # Ensure the partner is always a person, not a company
        # This maintains consistency across all partner creation scenarios
        partner_vals.update({
            'is_patient': True,
            'is_person': True,
            'is_company': False,
        })
        return partner_vals

# vim=expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
