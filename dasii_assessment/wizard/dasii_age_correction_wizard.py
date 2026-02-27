from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

class DasiiAgeCorrectionWizard(models.TransientModel):
    _name = 'dasii.age.correction.wizard'
    _description = 'Calculate Corrected Age'

    assessment_id = fields.Many2one('dasii.assessment', string="Assessment", required=True)
    dob = fields.Date(related='assessment_id.date_of_birth', string="Date of Birth")
    calculate_at_date = fields.Date(string="Calculate Corrected Age at", default=fields.Date.context_today, required=True)
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and 'assessment_id' in fields_list:
            res['assessment_id'] = active_id
        return res
        
    gestation_basis = fields.Selection([
        ('edd', 'Estimated date of delivery'),
        ('ga', 'Best estimate of gestational age'),
    ], string="Gestation at birth based on", required=True)

    edd_date = fields.Date(string="Best estimate of EDD")
    ga_weeks = fields.Integer(string="GA Estimate (Weeks)", help="Usually between 22 and 44 weeks")
    
    @api.onchange('gestation_basis')
    def _onchange_gestation_basis(self):
        if self.gestation_basis == 'edd':
            self.ga_weeks = False
        elif self.gestation_basis == 'ga':
            self.edd_date = False

    def action_calculate(self):
        self.ensure_one()
        assess = self.assessment_id
        
        corrected_months = 0.0
        
        if self.gestation_basis == 'edd' and self.edd_date:
            # Corrected Age = Date of Test - EDD
            delta = relativedelta(self.calculate_at_date, self.edd_date)
            corrected_months = delta.years * 12 + delta.months + (delta.days / 30.0)
            
        elif self.gestation_basis == 'ga' and self.ga_weeks:
            # Full term = 40 weeks. Prematurity gap = 40 - GA.
            # Convert gap to days (1 week = 7 days).
            prematurity_days = (40 - self.ga_weeks) * 7
            
            # Chronological Age = Date of Test - DOB
            delta_chrono = relativedelta(self.calculate_at_date, self.dob)
            chrono_days = (delta_chrono.years * 365.25) + (delta_chrono.months * 30.44) + delta_chrono.days
            
            # Corrected = Chrono - Prematurity
            corrected_days = chrono_days - prematurity_days
            corrected_months = corrected_days / 30.44
        
        # Ensure it doesn't go below 0
        if corrected_months < 0:
            corrected_months = 0.0
            
        # Update Assessment record
        assess.write({
            'is_premature': True,
            'corrected_age_months': corrected_months
        })
