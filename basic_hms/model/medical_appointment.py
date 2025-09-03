from odoo import api, fields, models, _
from datetime import datetime, date
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class medical_appointment(models.Model):

    _name = 'medical.appointment'
    _description = 'OPD Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'appointment_date desc'

    name = fields.Char(string='Appointment ID', readonly=True,
                       copy=True)
    is_invoiced = fields.Boolean(copy=False, default=False)
    institution_partner_id = fields.Many2one('res.partner',
            domain=[('is_institution', '=', True)],
            string='Health Center')
    # Removed inpatient_registration_id - model deleted
    patient_status = fields.Selection([('ambulatory', 'Ambulatory'),
            ('outpatient', 'Outpatient'), ('inpatient', 'Inpatient')],
            'Patient status', sort=False, default='outpatient')
    case_type = fields.Selection([('new', 'New'),
            ('revisit', 'Re-Visit')],
            'Case Type', default='new', tracking=True)
    patient_id = fields.Many2one('medical.patient', 'Patient',
                                 required=True, tracking=True)
    urgency_level = fields.Selection([('a', 'Normal'), ('b', 'Urgent'),
            ('c', 'Medical Emergency')], 'Urgency Level', sort=False,
            default='a')
    appointment_date = fields.Datetime('Appointment Date',
            required=True, default=fields.Datetime.now, tracking=True)
    appointment_end = fields.Datetime('Patient Exit time', tracking=True)
    doctor_id = fields.Many2one('medical.physician', 'Doctor',
                                required=True, default=lambda self: self._default_doctor_id())
    no_invoice = fields.Boolean(string='Invoice exempt', default=False)
    validity_status = fields.Selection([('invoice', 'Invoice'), ('tobe'
            , 'To be Invoiced')], 'Status', sort=False, readonly=True,
            default='tobe')
    appointment_validity_date = fields.Datetime('Validity Date', tracking=True)
    previous_appointment_date = fields.Datetime('Previous Appointment Date', compute='_compute_previous_appointment_days', store=True)
    # previous_appointment_days = fields.Char('Days ago', readonly=1)
    previous_appointment_days = fields.Char('Days ago', compute='_compute_previous_appointment_days', store=True)
    previous_appointment_count = fields.Integer('Previous Appointments', compute="_compute_appointment_count", default=0)
    consultations_id = fields.Many2one('product.template',
            'Case Product')
    comments = fields.Text(string='Info')
    invoice_to_insurer = fields.Boolean('Invoice to Insurance')
    # Removed medical_patient_psc_ids - model deleted
    # Removed medical_prescription_order_ids - model deleted
    # Removed insurer_id - model deleted
    therapy_ids = fields.Many2many('therapy.type', string='Therapies', tracking=True)
    duration = fields.Integer('Duration (Mins)')
    invoice_id = fields.Many2one("account.move", string="Invoice", readonly=True)
    state = fields.Selection([('pending','Pending'),('done','Completed')],string="State",default="pending", tracking=True)
    
    # Calendar and display fields
    therapy_names = fields.Char(string='Therapies', compute='_compute_therapy_names', store=True)
    calendar_color = fields.Char(string='Calendar Color', compute='_compute_calendar_color', store=True)
    attendance_date = fields.Date(string='Attendance Date', compute='_compute_attendance_date', store=True)
    
    @api.depends('therapy_ids')
    def _compute_therapy_names(self):
        """Compute therapy names for calendar display"""
        for record in self:
            if record.therapy_ids:
                record.therapy_names = ', '.join(record.therapy_ids.mapped('name'))
            else:
                record.therapy_names = 'General Consultation'
    
    @api.depends('therapy_ids')
    def _compute_calendar_color(self):
        """Compute calendar color based on therapy types"""
        for record in self:
            if not record.therapy_ids:
                record.calendar_color = '#1f77b4'  # Default blue
            elif len(record.therapy_ids) == 1:
                # Single therapy - use therapy-specific colors
                therapy = record.therapy_ids[0]
                if therapy.code == 'ST':
                    record.calendar_color = '#ff7f0e'  # Orange for Speech
                elif therapy.code == 'OT':
                    record.calendar_color = '#2ca02c'  # Green for Occupational
                elif therapy.code == 'PT':
                    record.calendar_color = '#d62728'  # Red for Physio
                else:
                    record.calendar_color = '#9467bd'  # Purple for others
            else:
                record.calendar_color = '#8c564b'  # Brown for multiple therapies
    
    @api.depends('appointment_date')
    def _compute_attendance_date(self):
        """Compute attendance date for calendar grouping"""
        for record in self:
            if record.appointment_date:
                record.attendance_date = record.appointment_date.date()
            else:
                record.attendance_date = False

    def action_end_appointment(self):
        """Set appointment_end to current datetime and calculate duration."""
        for record in self:
            end_time = fields.Datetime.now()
            duration = 0
            if record.appointment_date:
                duration = (end_time - record.appointment_date).total_seconds() / 60  # Convert seconds to minutes
            
            record.update({
                'appointment_end': end_time,
                'duration': int(duration),  # Store as an integer
                'state': 'done',
            })

    def action_open_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointments',
            'view_mode': 'list,form',
            'res_model': 'medical.appointment',
            'domain': [('patient_id', '=', self.patient_id.id), ('id', '!=', self.id)],
            'context': "{'create': False}"
        }

    def _compute_appointment_count(self):
        for record in self:
            record.previous_appointment_count = self.search_count([('patient_id', '=', self.patient_id.id), ('id', '!=', record.id)])

    @api.onchange('case_type')
    def _onchange_case_type(self):
        """Automatically set consultations_id based on case_type."""
        if self.case_type:
            product_mapping = {
                'new': self.env.ref('basic_hms.new_opd', raise_if_not_found=False),
                'existing': self.env.ref('basic_hms.old_opd', raise_if_not_found=False)
            }
            self.consultations_id = product_mapping.get(self.case_type, False)

    @api.depends('patient_id', 'appointment_date')
    def _compute_previous_appointment_days(self):
        for record in self:
            if record.patient_id:
                previous_appointment = self.env['medical.appointment'].search([
                    ('patient_id', '=', record.patient_id.id),
                    ('id', '!=', record.id)
                ], order='appointment_date DESC', limit=1)

                if previous_appointment:
                    record.previous_appointment_date = previous_appointment.appointment_date

                    # Calculate the days difference
                    if record.appointment_date and previous_appointment.appointment_date:
                        delta_days = (record.appointment_date.date() - previous_appointment.appointment_date.date()).days
                        record.previous_appointment_days = f"{delta_days} days" if delta_days >= 0 else "0 days"
                    else:
                        record.previous_appointment_days = "N/A"
                else:
                    record.previous_appointment_date = False
                    record.previous_appointment_days = "N/A"
            else:
                record.previous_appointment_days = "N/A"

    @api.model
    def _default_doctor_id(self):
        return self.env.ref('basic_hms.medical_physician_1', raise_if_not_found=False) or self.env['medical.physician'].search([], limit=1)

    def _valid_field_parameter(self, field, name):
        return name == 'sort' or super()._valid_field_parameter(field,
                name)

    # Removed onchange_name - model deleted

    @api.model_create_multi
    def create(self, vals_list):
        today_str = datetime.today().strftime("%d%m%y")
        for vals in vals_list:
            apt_id = self.env['ir.sequence' ].next_by_code('medical.appointment' ) or 'VISIT'
            vals['name'] = f"VISIT{today_str}-{apt_id}"
            msg_body = 'Visit created'
            for msg in self:
                msg.message_post(body=msg_body)
        return super(medical_appointment, self).create(vals_list)

    # Removed onchange_patient - field deleted

    def confirm(self):
        self.write({'state': 'confirmed'})

    def done(self):
        self.write({'state': 'done'})

    def cancel(self):
        self.write({'state': 'cancel'})

    def print_prescription(self):
        return self.env.ref('basic_hms.report_print_prescription'
                            ).report_action(self)

    def view_patient_invoice(self):
        self.write({'state': 'cancel'})

    def create_invoice(self):
        """Create invoice based on therapy types with commission calculation"""
        self.ensure_one()
        
        if self.is_invoiced:
            raise UserError(_('Invoice already exists for this appointment'))
        
        if self.no_invoice:
            raise UserError(_('This appointment is invoice exempt'))
        
        # Check if therapies are selected
        if not self.therapy_ids:
            raise UserError(_('No therapies selected for this appointment. Please select therapies before creating invoice.'))
        
        # Get sale journal
        sale_journals = self.env['account.journal'].search([('type', '=', 'sale')])
        if not sale_journals:
            raise UserError(_('No sale journal found. Please configure a sale journal.'))
        
        # Create invoice header
        invoice_vals = {
            'name': self.env['ir.sequence'].next_by_code('medical_app_therapy_inv_seq'),
            'invoice_origin': self.name or '',
            'move_type': 'out_invoice',
            'ref': False,
            'partner_id': self.patient_id.patient_id.id or False,
            'partner_shipping_id': self.patient_id.patient_id.id,
            'currency_id': self.patient_id.patient_id.currency_id.id,
            'invoice_payment_term_id': False,
            'fiscal_position_id': self.patient_id.patient_id.property_account_position_id.id,
            'team_id': False,
            'invoice_date': date.today(),
            'journal_id': sale_journals.id,
            'ref': self.name,
        }
        
        account_invoice_obj = self.env['account.move']
        invoice = account_invoice_obj.create(invoice_vals)
        
        # Create invoice lines for each therapy
        for therapy in self.therapy_ids:
            if not therapy.product_id:
                raise UserError(_('No product associated with therapy %s. Please configure product for this therapy type.') % therapy.name)
            
            # Get income account for the product
            invoice_line_account_id = False
            if therapy.product_id.id:
                invoice_line_account_id = (therapy.product_id.property_account_income_id.id or 
                                         therapy.product_id.categ_id.property_account_income_categ_id.id or 
                                         False)
            
            if not invoice_line_account_id:
                raise UserError(
                    _('There is no income account defined for product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                    (therapy.product_id.name,))
            
            # Get taxes
            tax_ids = []
            taxes = therapy.product_id.taxes_id.filtered(
                lambda r: not therapy.product_id.company_id or r.company_id == therapy.product_id.company_id)
            tax_ids = taxes.ids
            
            # Create invoice line
            invoice_line_vals = {
                'name': therapy.product_id.name or '',
                'account_id': invoice_line_account_id,
                'price_unit': therapy.product_id.list_price,
                'product_uom_id': therapy.product_id.uom_id.id,
                'quantity': 1,
                'product_id': therapy.product_id.id,
                'tax_ids': [(6, 0, tax_ids)],
                'therapy_type_id': therapy.id,  # Link to therapy type for commission calculation
            }
            
            # Add line to invoice
            invoice.write({'invoice_line_ids': [(0, 0, invoice_line_vals)]})
        
        # Mark appointment as invoiced
        self.write({
            'is_invoiced': True, 
            'invoice_id': invoice.id
        })
        
        # Return action to show created invoice
        imd = self.env['ir.model.data']
        action = self.env.ref('account.action_move_out_invoice_type')
        list_view_id = imd.sudo()._xmlid_to_res_id('account.view_invoice_tree')
        form_view_id = imd.sudo()._xmlid_to_res_id('account.view_move_form')
        
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'list'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        
        result['domain'] = "[('id','=',%s)]" % invoice.id
        
        return result


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
