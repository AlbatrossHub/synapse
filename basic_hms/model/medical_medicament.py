# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class medical_medicament(models.Model):
  
    _name = 'medical.medicament'
    _description = 'Medical Medicament'
    _rec_name = 'medical_name'

    @api.depends('product_id')
    def onchange_product(self):
        for each in self:
            if each:
                self.qty_available = self.product_id.qty_available
                self.price = self.product_id.lst_price
            else:
                self.qty_available = 0
                self.price = 0.0

    medical_name = fields.Text('Name')
    product_id  = fields.Many2one('product.product', 'Product', required=True)
    therapeutic_action = fields.Char('Therapeutic effect', help = 'Therapeutic action')
    price = fields.Float(compute=onchange_product,string='Price',store=True)
    qty_available = fields.Integer(compute=onchange_product,string='Quantity Available',store=True)
    indications = fields.Text('Indications')
    active_component = fields.Char(string="Active Component")
    presentation = fields.Text('Presentation')
    composition = fields.Text('Composition')
    dosage = fields.Text('Dosage Instructions')
    overdosage = fields.Text('Overdosage')