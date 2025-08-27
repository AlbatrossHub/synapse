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
