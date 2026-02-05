from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

class DasiiAssessment(models.Model):
    _name = 'dasii.assessment'
    _description = 'DASII Assessment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one('res.partner', string='Patient', required=True, tracking=True)
    assessment_date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    date_of_birth = fields.Date(string='Date of Birth', required=True, tracking=True)
    
    # Computed Age
    age_months = fields.Float(string='Age (Months)', compute='_compute_age', store=True)
    
    line_ids = fields.One2many('dasii.assessment.line', 'assessment_id', string='Assessment Lines')
    cluster_score_ids = fields.One2many('dasii.cluster.score', 'assessment_id', string='Cluster Scores')
    
    @api.depends('date_of_birth', 'assessment_date')
    def _compute_age(self):
        for record in self:
            if record.date_of_birth and record.assessment_date:
                # Calculate age in months accurately
                # relativedelta(date1, date2) gives years, months, days
                # We can approximate or be exact. DASII uses months.
                delta = relativedelta(record.assessment_date, record.date_of_birth)
                record.age_months = delta.years * 12 + delta.months + (delta.days / 30.0)
            else:
                record.age_months = 0.0

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            # Safe check if dob exists on partner (soft dependency)
            if hasattr(self.partner_id, 'dob'):
                self.date_of_birth = self.partner_id.dob

    def action_load_items(self):
        """Loads all items into the assessment if not already present."""
        self.ensure_one()
        # Find all items - Sorted by Scale then Item No
        # _order is 'scale desc, item_no asc' in dasii.item now
        all_items = self.env['dasii.item'].search([]) 
        
        # Existing items in this assessment
        existing_item_ids = self.line_ids.mapped('item_id.id')
        
        lines_to_create = []
        for item in all_items:
            if item.id not in existing_item_ids:
                lines_to_create.append({
                    'assessment_id': self.id,
                    'item_id': item.id,
                    'item_scale': item.scale,
                })
        
        if lines_to_create:
            self.env['dasii.assessment.line'].create(lines_to_create)

    def action_calculate_score(self):
        """Calculates the cluster scores based on PASS (Yes) answers."""
        for record in self:
            # Clear existing scores
            record.cluster_score_ids.unlink()
            
            # Find all relevant clusters
            clusters = self.env['dasii.cluster'].search([])
            
            score_vals = []
            for cluster in clusters:
                # Find lines associated with items in this cluster
                cluster_lines = record.line_ids.filtered(lambda l: l.item_id.cluster_id == cluster)
                
                total_items = len(cluster_lines)
                yes_count = len(cluster_lines.filtered(lambda l: l.status == 'yes'))
                
                if total_items > 0:
                    score_vals.append({
                        'assessment_id': record.id,
                        'cluster_id': cluster.id,
                        'total_items': total_items,
                        'yes_count': yes_count,
                    })
            
            if score_vals:
                self.env['dasii.cluster.score'].create(score_vals)


class DasiiAssessmentLine(models.Model):
    _name = 'dasii.assessment.line'
    _description = 'DASII Assessment Line'
    _order = 'item_scale desc, item_no asc'

    assessment_id = fields.Many2one('dasii.assessment', required=True, ondelete='cascade')
    item_id = fields.Many2one('dasii.item', required=True, ondelete='restrict')
    
    # Related fields for grouping and view convenience
    item_no = fields.Integer(related='item_id.item_no', string='Item No', readonly=True, store=True)
    item_description = fields.Text(related='item_id.description', string='Description', readonly=True)
    item_scale = fields.Selection(related='item_id.scale', string='Scale', store=True, readonly=True)
    
    status = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Status')
    
    comments = fields.Text()
