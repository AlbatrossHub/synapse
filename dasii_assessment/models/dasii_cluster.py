from odoo import models, fields

class DasiiCluster(models.Model):
    _name = 'dasii.cluster'
    _description = 'DASII Cluster'
    _order = 'scale, sequence, id'

    name = fields.Char(required=True)
    code = fields.Char()
    scale = fields.Selection([
        ('motor', 'Motor Development'),
        ('mental', 'Mental Development'),
    ], required=True, string='Scale Type')
    sequence = fields.Integer(default=10)
    item_ids = fields.One2many('dasii.item', 'cluster_id', string='Items')
