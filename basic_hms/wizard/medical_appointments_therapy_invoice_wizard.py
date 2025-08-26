# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime


class MedicalAppointmentsTherapyInvoiceWizard(models.TransientModel):
    _name = "medical.appointments.therapy.invoice.wizard"
    _description = 'Medical Appointments Therapy Invoice Wizard'

    def create_therapy_invoice(self):
        """Create invoice based on therapy types with commission calculation"""
        active_ids = self._context.get('active_ids')
        if not active_ids:
            raise UserError(_('No appointments selected for invoicing.'))

        list_of_invoice_ids = []
        appointment_obj = self.env['medical.appointment']
        account_invoice_obj = self.env['account.move']
        
        for active_id in active_ids:
            appointment = appointment_obj.browse(active_id)
            
            # Check if already invoiced
            if appointment.is_invoiced:
                raise UserError(_('Appointment %s is already invoiced.') % appointment.name)
            
            # Check if invoice exempt
            if appointment.no_invoice:
                raise UserError(_('Appointment %s is invoice exempt.') % appointment.name)
            
            # Check if therapies are selected
            if not appointment.therapy_ids:
                raise UserError(_('No therapies selected for appointment %s.') % appointment.name)
            
            # Get sale journal
            sale_journals = self.env['account.journal'].search([('type', '=', 'sale')])
            if not sale_journals:
                raise UserError(_('No sale journal found. Please configure a sale journal.'))
            
            # Create invoice header
            invoice_vals = {
                'name': self.env['ir.sequence'].next_by_code('medical_app_therapy_inv_seq'),
                'invoice_origin': appointment.name or '',
                'move_type': 'out_invoice',
                'ref': False,
                'partner_id': appointment.patient_id.patient_id.id or False,
                'partner_shipping_id': appointment.patient_id.patient_id.id,
                'currency_id': appointment.patient_id.patient_id.currency_id.id,
                'invoice_payment_term_id': False,
                'fiscal_position_id': appointment.patient_id.patient_id.property_account_position_id.id,
                'team_id': False,
                'invoice_date': date.today(),
                'journal_id': sale_journals.id,
                'ref': appointment.name,
            }
            
            invoice = account_invoice_obj.create(invoice_vals)
            
            # Create invoice lines for each therapy
            for therapy in appointment.therapy_ids:
                if not therapy.product_id:
                    raise UserError(_('No product associated with therapy %s.') % therapy.name)
                
                # Get income account for the product
                invoice_line_account_id = False
                if therapy.product_id.id:
                    invoice_line_account_id = (therapy.product_id.property_account_income_id.id or 
                                             therapy.product_id.categ_id.property_account_income_categ_id.id or 
                                             False)
                
                if not invoice_line_account_id:
                    raise UserError(
                        _('There is no income account defined for product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                        (therapy.product_id.name,))
                
                # Get taxes
                tax_ids = []
                taxes = therapy.product_id.taxes_id.filtered(
                    lambda r: not therapy.product_id.company_id or r.company_id == therapy.product_id.company_id)
                tax_ids = taxes.ids
                
                # Create invoice line
                invoice_line_vals = {
                    'name': therapy.product_id.name or '',
                    'account_id': invoice_line_account_id,
                    'price_unit': therapy.product_id.list_price,
                    'product_uom_id': therapy.product_id.uom_id.id,
                    'quantity': 1,
                    'product_id': therapy.product_id.id,
                    'tax_ids': [(6, 0, tax_ids)],
                    'therapy_type_id': therapy.id,  # Link to therapy type for commission calculation
                }
                
                # Add line to invoice
                invoice.write({'invoice_line_ids': [(0, 0, invoice_line_vals)]})
            
            # Mark appointment as invoiced
            appointment.write({
                'is_invoiced': True, 
                'invoice_id': invoice.id
            })
            
            list_of_invoice_ids.append(invoice.id)
        
        # Return action to show created invoices
        if list_of_invoice_ids:
            imd = self.env['ir.model.data']
            action = self.env.ref('account.action_move_out_invoice_type')
            list_view_id = imd.sudo()._xmlid_to_res_id('account.view_invoice_tree')
            form_view_id = imd.sudo()._xmlid_to_res_id('account.view_move_form')
            
            result = {
                'name': action.name,
                'help': action.help,
                'type': action.type,
                'views': [[list_view_id, 'list'], [form_view_id, 'form']],
                'target': action.target,
                'context': action.context,
                'res_model': action.res_model,
            }
            
            if list_of_invoice_ids:
                result['domain'] = "[('id','in',%s)]" % list_of_invoice_ids
            
            return result
        
        return {'type': 'ir.actions.act_window_close'}
