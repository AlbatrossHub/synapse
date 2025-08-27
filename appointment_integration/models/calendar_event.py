from odoo import models, fields, api


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    # Sync flag to track if this event has been processed for medical appointment
    is_computed_as_medical_appointment = fields.Boolean(
        string='Synced to Medical Appointment',
        default=False,
        help='Indicates if this calendar event has been synchronized to create a medical appointment'
    )
