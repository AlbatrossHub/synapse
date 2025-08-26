# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    commission = fields.Float(string='Commission', compute='_compute_commission', store=True)
    therapy_type_id = fields.Many2one('therapy.type', string='Therapy Type')

    @api.depends('product_id', 'price_unit', 'quantity', 'therapy_type_id')
    def _compute_commission(self):
        """Compute commission based on therapy type and product"""
        for line in self:
            commission = 0.0
            if line.therapy_type_id and line.price_unit and line.quantity:
                therapy = line.therapy_type_id
                if therapy.commission_type == 'fixed':
                    commission = therapy.commission_value
                elif therapy.commission_type == 'percentage':
                    total_amount = line.price_unit * line.quantity
                    commission = (total_amount * therapy.commission_value) / 100.0
            line.commission = commission
