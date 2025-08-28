from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MedicalPatient(models.Model):
    _inherit = 'medical.patient'

    def action_sync_appointments(self):
        """Sync calendar events to create medical appointments"""
        self.ensure_one()
        
        if not self.patient_id:
            raise UserError(_('No patient partner associated with this medical patient record.'))
        
        # Find unprocessed calendar events for this patient
        calendar_events = self.env['calendar.event'].search([
            ('partner_ids', 'in', self.patient_id.id),
            ('is_computed_as_medical_appointment', '=', False)
        ])
        
        if not calendar_events:
            raise UserError(_('No unprocessed calendar events found for this patient.'))
        
        # Group events by date
        events_by_date = {}
        for event in calendar_events:
            event_date = event.start.date() if event.start else fields.Date.today()
            if event_date not in events_by_date:
                events_by_date[event_date] = []
            events_by_date[event_date].append(event)
        
        created_appointments = []
        
        # Create medical appointments for each date
        for appointment_date, events in events_by_date.items():
            # Collect all therapy types from all events on this date
            all_therapy_ids = []
            appointment_comments = []
            
            for event in events:
                # Mark event as processed
                event.is_computed_as_medical_appointment = True
                
                # Add event name to comments
                appointment_comments.append(f"Calendar Event: {event.name}")
                
                # Get therapy types based on appointment type or resource names
                therapy_ids = self._get_therapy_ids_from_event(event)
                if therapy_ids:
                    all_therapy_ids.extend(therapy_ids)
                    appointment_comments.append(f"Therapies: {', '.join(self.env['therapy.type'].browse(therapy_ids).mapped('name'))}")
                else:
                    appointment_comments.append("No specific therapy identified")
            
            # Remove duplicates from therapy IDs
            all_therapy_ids = list(set(all_therapy_ids))
            
            # Create medical appointment
            medical_appointment = self.env['medical.appointment'].create({
                'patient_id': self.id,
                'doctor_id': events[0].user_id.id if events[0].user_id else False,
                'appointment_date': appointment_date,
                'state': 'pending',
                'therapy_ids': [(6, 0, all_therapy_ids)],
                'comments': '\n'.join(appointment_comments),
            })
            
            created_appointments.append(medical_appointment)
        
        # Show success message
        if created_appointments:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sync Completed'),
                    'message': _('Successfully created %d medical appointment(s) from %d calendar event(s).') % (
                        len(created_appointments), len(calendar_events)
                    ),
                    'type': 'success',
                    'sticky': False,
                }
            }
        
        return True

    def _get_therapy_ids_from_event(self, event):
        """Extract therapy IDs from calendar event resources"""
        therapy_ids = []
        
        # Get therapy types from appointment resources
        if hasattr(event, 'appointment_resource_ids') and event.appointment_resource_ids:
            for resource in event.appointment_resource_ids:
                # Find therapy type linked to this resource
                therapy = self.env['therapy.type'].search([
                    ('appointment_resource_id', '=', resource.id)
                ], limit=1)
                
                if therapy and therapy.id not in therapy_ids:
                    therapy_ids.append(therapy.id)
        
        return therapy_ids

    def action_create_consolidated_invoice(self):
        """Create a consolidated invoice for all unpaid appointments of this patient"""
        self.ensure_one()
        
        # Find all medical appointments for this patient without invoices
        unpaid_appointments = self.env['medical.appointment'].search([
            ('patient_id', '=', self.id),
            ('invoice_id', '=', False),
            ('state', '!=', 'cancelled')  # Exclude cancelled appointments
        ])
        
        if not unpaid_appointments:
            raise UserError(_('No unpaid appointments found for this patient.'))
        
        # Group therapies by product to consolidate quantities
        therapy_consolidation = {}
        
        for appointment in unpaid_appointments:
            for therapy in appointment.therapy_ids:
                if not therapy.product_id:
                    raise UserError(_('Therapy "%s" does not have an associated product. Please configure products for all therapies.') % therapy.name)
                
                product_id = therapy.product_id.id
                if product_id not in therapy_consolidation:
                    therapy_consolidation[product_id] = {
                        'product': therapy.product_id,
                        'quantity': 0,
                        'therapy_type_id': therapy.id
                    }
                therapy_consolidation[product_id]['quantity'] += 1
        
        # Create the consolidated invoice
        sale_journals = self.env['account.journal'].search([('type', '=', 'sale')])
        if not sale_journals:
            raise UserError(_('No sale journal found. Please configure a sale journal.'))
        
        # Get patient partner
        if not self.patient_id:
            raise UserError(_('No patient partner associated with this medical patient record.'))
        
        # Create invoice header
        invoice_vals = {
            'name': self.env['ir.sequence'].next_by_code('medical_consolidated_inv_seq'),
            'invoice_origin': f'Consolidated Invoice - {self.name}',
            'move_type': 'out_invoice',
            'ref': False,
            'partner_id': self.patient_id.id,
            'partner_shipping_id': self.patient_id.id,
            'currency_id': self.patient_id.currency_id.id,
            'invoice_payment_term_id': False,
            'fiscal_position_id': self.patient_id.property_account_position_id.id,
            'team_id': False,
            'invoice_date': fields.Date.today(),
            'journal_id': sale_journals.id,
            'state': 'draft',  # Keep as draft
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        # Create invoice lines for consolidated therapies
        for product_id, consolidation_data in therapy_consolidation.items():
            product = consolidation_data['product']
            quantity = consolidation_data['quantity']
            therapy_type_id = consolidation_data['therapy_type_id']
            
            # Get account
            invoice_line_account_id = (product.property_account_income_id.id or
                                      product.categ_id.property_account_income_categ_id.id or
                                      False)
            
            if not invoice_line_account_id:
                raise UserError(
                    _('There is no income account defined for product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                    (product.name,))
            
            # Get taxes
            tax_ids = []
            taxes = product.taxes_id.filtered(
                lambda r: not product.company_id or r.company_id == product.company_id)
            tax_ids = taxes.ids
            
            # Create invoice line
            invoice_line_vals = {
                'name': f"{product.name} (Consolidated - {quantity} sessions)",
                'account_id': invoice_line_account_id,
                'price_unit': product.list_price,
                'quantity': quantity,
                'product_uom_id': product.uom_id.id,
                'product_id': product.id,
                'tax_ids': [(6, 0, tax_ids)],
                'therapy_type_id': therapy_type_id,
            }
            
            invoice.write({'invoice_line_ids': [(0, 0, invoice_line_vals)]})
        
        # Update all related appointments with the new invoice
        unpaid_appointments.write({
            'invoice_id': invoice.id,
            'is_invoiced': True
        })
        
        # Create a clean log message with proper formatting
        therapy_lines_text = ""
        for product_id, consolidation_data in therapy_consolidation.items():
            product = consolidation_data['product']
            quantity = consolidation_data['quantity']
            total_line_amount = product.list_price * quantity
            therapy_lines_text += f"• {product.name}: {quantity} session(s) × {invoice.currency_id.symbol}{product.list_price:.2f} = {invoice.currency_id.symbol}{total_line_amount:.2f}\n"
        
        log_message = f"""
Consolidated Invoice Created

Successfully created consolidated invoice for {len(unpaid_appointments)} appointment(s) with {len(therapy_consolidation)} therapy line(s).

Invoice Details:
• Invoice Number: {invoice.name}
• Total Amount: {invoice.currency_id.symbol}{invoice.amount_total:.2f}
• Status: Draft

Consolidated Therapy Lines:
{therapy_lines_text}
Invoice Reference: {invoice.name} (ID: {invoice.id})
        """
        
        # Add the log note to the patient record
        self.message_post(
            body=log_message,
            subject=_('Consolidated Invoice Created'),
            message_type='notification'
        )
        
        # Show success message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Consolidated Invoice Created'),
                'message': _('Successfully created consolidated invoice for %d appointment(s) with %d therapy line(s). Check the chatter for details.') % (
                    len(unpaid_appointments), len(therapy_consolidation)
                ),
                'type': 'success',
                'sticky': False,
            }
        }
