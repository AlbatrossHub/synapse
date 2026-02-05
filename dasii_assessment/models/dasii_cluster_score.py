from odoo import models, fields

class DasiiClusterScore(models.Model):
    _name = 'dasii.cluster.score'
    _description = 'DASII Cluster Score'
    _order = 'cluster_scale, cluster_id'

    assessment_id = fields.Many2one('dasii.assessment', required=True, ondelete='cascade')
    cluster_id = fields.Many2one('dasii.cluster', required=True, readonly=True)
    
    cluster_name = fields.Char(related='cluster_id.name', readonly=True)
    cluster_scale = fields.Selection(related='cluster_id.scale', readonly=True, store=True)
    
    total_items = fields.Integer(string='Total')
    yes_count = fields.Integer(string='RESULT')
