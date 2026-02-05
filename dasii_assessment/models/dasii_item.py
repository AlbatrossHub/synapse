from odoo import models, fields, api

class DasiiItem(models.Model):
    _name = 'dasii.item'
    _description = 'DASII Item'
    _order = 'scale desc, item_no asc'

    item_no = fields.Integer(string='Item No', required=True)
    
    description = fields.Text(required=True)
    scale = fields.Selection([
        ('motor', 'Motor Development'),
        ('mental', 'Mental Development'),
    ], required=True)
    
    age_50 = fields.Float(string='50% Pass Age (Months)')
    age_3 = fields.Float(string='3% Pass Age (Months)')
    age_97 = fields.Float(string='97% Pass Age (Months)')
    
    cluster_id = fields.Many2one('dasii.cluster', string='Cluster')
    
    _sql_constraints = [
        ('item_scale_uniq', 'unique(item_no, scale)', 'Item number must be unique per scale!'),
    ]
