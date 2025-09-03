# -*- coding: utf-8 -*-
# Part of Synapse Clinic. See LICENSE file for full copyright and licensing details.

import base64
import io
import xlsxwriter
from collections import defaultdict

from odoo import _, fields, models
from odoo.exceptions import UserError


class TherapyReportWizard(models.TransientModel):
    _name = 'therapy.report.wizard'
    _description = 'Therapy Report Wizard'

    date_start = fields.Date(string="Start Date", default=fields.Date.context_today)
    date_end = fields.Date(string="End Date", default=fields.Date.context_today)
    therapy_type_ids = fields.Many2many('therapy.type', string="Therapy Types", 
                                       help="Leave empty to include all therapy types")
    generated_xlsx_file = fields.Binary(string="Generated XLSX Report")

    def action_generate_xlsx_report(self):
        """Generate XLSX report with therapy data and commission calculations"""
        
        # Build domain for medical appointments
        domain = [('state', '!=', 'cancelled')]
        if self.date_start:
            domain += [('appointment_date', '>=', self.date_start)]
        if self.date_end:
            domain += [('appointment_date', '<=', self.date_end)]

        # Get all medical appointments in the date range
        appointments = self.env['medical.appointment'].sudo().search(domain, order='appointment_date DESC')

        if not appointments:
            raise UserError(_("No appointment records were found for the specified date range."))

        # Get all therapy types (either selected or all)
        if self.therapy_type_ids:
            therapy_types = self.therapy_type_ids
        else:
            therapy_types = self.env['therapy.type'].search([('active', '=', True)])

        if not therapy_types:
            raise UserError(_("No therapy types found. Please configure therapy types first."))

        # Get all invoices related to these appointments
        invoice_ids = appointments.mapped('invoice_id').filtered(lambda inv: inv.state in ['posted', 'draft'])
        
        if not invoice_ids:
            raise UserError(_("No invoices found for the appointments in the specified date range."))

        # Create Excel workbook
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Therapy Report')

        # Define formats
        bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        header_format = workbook.add_format({
            'bold': True, 
            'bg_color': '#4F81BD', 
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd', 'align': 'center'})
        number_format = workbook.add_format({'num_format': '#,##0.00', 'align': 'right'})
        currency_format = workbook.add_format({'num_format': '₹#,##0.00', 'align': 'right'})
        total_format = workbook.add_format({
            'bold': True, 
            'bg_color': '#D9E1F2', 
            'num_format': '₹#,##0.00',
            'align': 'right'
        })

        # Set column widths
        worksheet.set_column(0, 0, 25)  # Invoice Partner
        worksheet.set_column(1, 1, 15)  # Invoice Number
        worksheet.set_column(2, 2, 12)  # Invoice Date
        
        # Dynamic columns for therapy types
        therapy_start_col = 3
        for therapy in therapy_types:
            col_width = max(len(therapy.name) + 5, 20)
            worksheet.set_column(therapy_start_col, therapy_start_col + 1, col_width)
            therapy_start_col += 2
        
        # Commission total column
        worksheet.set_column(therapy_start_col, therapy_start_col, 20)

        # Write main headers
        headers = ['Invoice Partner', 'Invoice Number', 'Invoice Date']
        
        # Add therapy type headers (2 columns each: Total Value + Commission)
        for therapy in therapy_types:
            headers.append(f'{therapy.name} - Total')
            headers.append(f'{therapy.name} - Commission')
        
        # Add commission total header
        headers.append('Total Commission')

        # Write main headers with formatting
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        # Write sub-headers for therapy columns
        sub_headers = ['', '', '']  # First 3 columns don't need sub-headers
        
        for therapy in therapy_types:
            sub_headers.append('Total Value')
            sub_headers.append('Commission')
        
        sub_headers.append('')  # Commission total column
        
        for col, sub_header in enumerate(sub_headers):
            if sub_header:  # Only write sub-headers for therapy columns
                worksheet.write(1, col, sub_header, bold)

        # Process data and write to Excel
        row = 2
        total_commission = 0.0
        
        for invoice in invoice_ids:
            # Get invoice lines with therapy data
            invoice_lines = invoice.invoice_line_ids.filtered(lambda line: line.therapy_type_id)
            
            if not invoice_lines:
                continue
            
            # Group invoice lines by therapy type
            therapy_data = defaultdict(lambda: {'total_value': 0.0, 'commission': 0.0})
            
            for line in invoice_lines:
                if line.therapy_type_id in therapy_types:
                    therapy_data[line.therapy_type_id]['total_value'] += line.price_subtotal
                    therapy_data[line.therapy_type_id]['commission'] += line.commission or 0.0
            
            # Calculate row commission total
            row_commission = sum(data['commission'] for data in therapy_data.values())
            total_commission += row_commission
            
            # Write invoice basic info
            worksheet.write(row, 0, invoice.partner_id.name or '')
            worksheet.write(row, 1, invoice.name or '')
            
            # Handle appointment_date (might be datetime or date)
            appointment_date = None
            if invoice.invoice_line_ids:
                # Get the first appointment related to this invoice
                first_appointment = appointments.filtered(lambda apt: apt.invoice_id == invoice)[:1]
                if first_appointment and first_appointment.appointment_date:
                    if hasattr(first_appointment.appointment_date, 'date'):
                        appointment_date = first_appointment.appointment_date.date()
                    else:
                        appointment_date = first_appointment.appointment_date
            
            worksheet.write(row, 2, appointment_date or '', date_format)
            
            # Write therapy data
            col = 3
            for therapy in therapy_types:
                data = therapy_data.get(therapy, {'total_value': 0.0, 'commission': 0.0})
                
                # Total Value column
                worksheet.write(row, col, data['total_value'], currency_format)
                col += 1
                
                # Commission column
                worksheet.write(row, col, data['commission'], currency_format)
                col += 1
            
            # Write row commission total
            worksheet.write(row, col, row_commission, total_format)
            
            row += 1

        # Write summary row
        if row > 2:  # Only if we have data
            summary_row = row
            
            # Write summary headers
            worksheet.write(summary_row, 0, 'TOTALS', bold)
            worksheet.write(summary_row, 1, '', bold)
            worksheet.write(summary_row, 2, '', bold)
            
            # Calculate and write therapy totals
            col = 3
            for therapy in therapy_types:
                # Calculate column totals
                col_total = 0.0
                col_commission = 0.0
                
                for data_row in range(2, row):
                    try:
                        col_total += worksheet.read(data_row, col) or 0.0
                        col_commission += worksheet.read(data_row, col + 1) or 0.0
                    except:
                        pass  # Handle any read errors
                
                # Write totals
                worksheet.write(summary_row, col, col_total, total_format)
                col += 1
                worksheet.write(summary_row, col, col_commission, total_format)
                col += 1
            
            # Write grand total commission
            worksheet.write(summary_row, col, total_commission, total_format)

        # Add filters info
        info_row = summary_row + 2 if row > 2 else row + 2
        worksheet.write(info_row, 0, f'Report Generated: {fields.Date.today()}', bold)
        worksheet.write(info_row + 1, 0, f'Date Range: {self.date_start or "All"} to {self.date_end or "All"}', bold)
        if self.therapy_type_ids:
            therapy_names = ', '.join(self.therapy_type_ids.mapped('name'))
            worksheet.write(info_row + 2, 0, f'Therapy Types: {therapy_names}', bold)

        workbook.close()
        output.seek(0)

        # Store the generated file
        self.generated_xlsx_file = base64.b64encode(output.getvalue())

        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": "/web/content?model=therapy.report.wizard"
                   "&field=generated_xlsx_file"
                   "&download=true"
                   "&filename={filename}"
                   "&id={record_id}".format(
                       filename=f'Therapy Report {fields.Date.today().strftime("%d-%b-%Y")}.xlsx',
                       record_id=self.id
                   ),
        }
