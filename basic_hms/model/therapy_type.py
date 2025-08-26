# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class therapy_type(models.Model):
    _name = 'therapy.type'
    _description = 'Therapy Type'
    _rec_name = 'name'

    name = fields.Char(string='Therapy Type', required=True)
    code = fields.Char(string='Code', required=True)
    product_id = fields.Many2one('product.template', string='Product', required=True, 
                                domain=[('type', '=', 'service')])
    commission_type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage')
    ], string='Commission Type', required=True, default='fixed')
    commission_value = fields.Float(string='Commission Value', required=True)
    active = fields.Boolean(string='Active', default=True)
    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Therapy Type code must be unique!')
    ]

    @api.onchange('commission_type')
    def _onchange_commission_type(self):
        """Reset commission value when commission type changes"""
        if self.commission_type:
            self.commission_value = 0.0

    def name_get(self):
        """Custom name display with code"""
        result = []
        for record in self:
            name = f"{record.code} - {record.name}"
            result.append((record.id, name))
        return result


