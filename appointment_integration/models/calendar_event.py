from odoo import models, fields, api


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    # Sync flag to track if this event has been processed for medical appointment
    is_computed_as_medical_appointment = fields.Boolean(
        string='Synced to Medical Appointment',
        default=False,
        help='Indicates if this calendar event has been synchronized to create a medical appointment'
    )

    @api.onchange('partner_ids', 'resource_ids')
    def _onchange_partner_resource_name(self):
        """Auto-calculate appointment name based on partner and resource selection"""
        if self.partner_ids and self.resource_ids:
            # Get the first partner name
            partner_name = self.partner_ids[0].name if self.partner_ids else ''
            
            # Get the first resource name
            resource_name = self.resource_ids[0].name if self.resource_ids else ''
            
            if partner_name and resource_name:
                # Format: "Resource Name for Partner Name"
                self.name = f"{resource_name} for {partner_name}"
            elif resource_name:
                # If only resource is selected
                self.name = f"{resource_name} Appointment"
            elif partner_name:
                # If only partner is selected
                self.name = f"Appointment for {partner_name}"
        elif self.partner_ids:
            # Only partner selected
            partner_name = self.partner_ids[0].name
            self.name = f"Appointment for {partner_name}"
        elif self.resource_ids:
            # Only resource selected
            resource_name = self.resource_ids[0].name
            self.name = f"{resource_name} Appointment"
        else:
            # Neither selected, clear the name
            self.name = ''
