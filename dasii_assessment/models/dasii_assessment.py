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
    
    # Scoring Fields
    motor_raw_score = fields.Integer(string='Motor Raw Score', readonly=True)
    mental_raw_score = fields.Integer(string='Mental Raw Score', readonly=True)
    
    motor_da = fields.Float(string='Motor DA (Months)', readonly=True, help="Developmental Age based on Total Score")
    mental_da = fields.Float(string='Mental DA (Months)', readonly=True, help="Developmental Age based on Total Score")
    
    motor_dq = fields.Float(string='Motor DQ', readonly=True, help="(DA / Chronological Age) * 100")
    mental_dq = fields.Float(string='Mental DQ', readonly=True, help="(DA / Chronological Age) * 100")
    
    # Corrected Age Fields
    is_premature = fields.Boolean(string='Is Premature?', default=False, readonly=True, tracking=True)
    corrected_age_months = fields.Float(string='Corrected Age (Months)', readonly=True, tracking=True)
    
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

    def _calculate_scale_score(self, scale):
        """
        Calculates score for a specific scale (motor/mental).
        Logic:
        1. Sort lines by Item No.
        2. Iterate: Count YES. 
        3. Stop if 10 consecutive NOs.
        4. Return total YES count found before stop.
        """
        self.ensure_one()
        lines = self.line_ids.filtered(lambda l: l.item_scale == scale).sorted('item_no')
        
        raw_score = 0
        consecutive_no = 0
        
        for line in lines:
            if line.status == 'yes':
                raw_score += 1
                consecutive_no = 0 # Reset on Yes
            elif line.status == 'no':
                consecutive_no += 1
            
            # Stop condition
            if consecutive_no >= 10:
                break
                
        return raw_score

    def action_calculate_score(self):
        """Calculates the cluster scores and Final DQ based on PASS (Yes) answers."""
        for record in self:
            # 1. Cluster Scores
            # Clear existing scores
            record.cluster_score_ids.unlink()
            
            # Find all relevant clusters
            clusters = self.env['dasii.cluster'].search([])
            
            score_vals = []
            for cluster in clusters:
                # Find lines associated with items in this cluster
                cluster_lines = record.line_ids.filtered(lambda l: l.item_id.cluster_id == cluster)
                
                total_items = len(cluster_lines)
                # Note: Cluster score is simple YES count, doesn't mention ceiling rule 
                # but usually cluster count is derived from effective items. 
                # For now keeping it simple count as originally requested.
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

            # 2. Final DQ Scoring
            motor_score = record._calculate_scale_score('motor')
            mental_score = record._calculate_scale_score('mental')
            
            record.motor_raw_score = motor_score
            record.mental_raw_score = mental_score
            
            # Determine DA (Developmental Age)
            # Find item with item_no == raw_score
            motor_da_item = self.env['dasii.item'].search([('scale', '=', 'motor'), ('item_no', '=', motor_score)], limit=1)
            mental_da_item = self.env['dasii.item'].search([('scale', '=', 'mental'), ('item_no', '=', mental_score)], limit=1)
            
            record.motor_da = motor_da_item.age_50 if motor_da_item else 0.0
            record.mental_da = mental_da_item.age_50 if mental_da_item else 0.0
            
            # Calculate DQ
            # Use corrected age if available and greater than 0
            effective_age = record.corrected_age_months if record.is_premature and record.corrected_age_months > 0 else record.age_months
            
            if effective_age > 0:
                record.motor_dq = (record.motor_da / effective_age) * 100
                record.mental_dq = (record.mental_da / effective_age) * 100
            else:
                record.motor_dq = 0.0
                record.mental_dq = 0.0

    def action_bulk_mark_yes(self):
        """Marks selected lines as Yes and unchecks them."""
        for record in self:
            selected_lines = record.line_ids.filtered(lambda l: l.is_selected)
            if selected_lines:
                selected_lines.write({'status': 'yes', 'is_selected': False})

    def action_bulk_mark_no(self):
        """Marks selected lines as No and unchecks them."""
        for record in self:
            selected_lines = record.line_ids.filtered(lambda l: l.is_selected)
            if selected_lines:
                selected_lines.write({'status': 'no', 'is_selected': False})


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
    
    is_selected = fields.Boolean(string='Select')

    status = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Status')
    
    comments = fields.Text()

    def action_mark_yes(self):
        self.status = 'yes'

    def action_mark_no(self):
        self.status = 'no'
