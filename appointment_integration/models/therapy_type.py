from odoo import models, fields, api


class TherapyType(models.Model):
    _inherit = 'therapy.type'

    # Link to appointment resource for calendar event mapping
    appointment_resource_id = fields.Many2one(
        'appointment.resource',
        string='Appointment Resource',
        help='Link this therapy type to a specific appointment resource for automatic mapping from calendar events'
    )


