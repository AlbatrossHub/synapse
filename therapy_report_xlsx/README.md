# Therapy Report XLSX Module

## Overview
This module generates comprehensive Excel reports for medical appointments with therapy data, including commission calculations based on therapy type configurations.

## Features
- **Date Range Filtering**: Generate reports for specific date periods
- **Therapy Type Filtering**: Optionally filter by specific therapy types
- **Dynamic Columns**: Automatically creates columns for each therapy type
- **Commission Calculation**: Shows both total value and commission for each therapy
- **Professional Formatting**: Clean, professional Excel output with proper formatting

## Excel Report Structure

### Column Layout
The generated Excel file will have the following structure:

| Column | Description |
|--------|-------------|
| A | Invoice Partner (Patient Name) |
| B | Invoice Number |
| C | Invoice Date |
| D | Therapy 1 - Total Value |
| E | Therapy 1 - Commission |
| F | Therapy 2 - Total Value |
| G | Therapy 2 - Commission |
| ... | ... (continues for each therapy type) |
| Last | Total Commission (sum of all commissions) |

### Example Output
```
Invoice Partner    | Invoice Number | Invoice Date | Speech Therapy - Total | Speech Therapy - Commission | Occupational Therapy - Total | Occupational Therapy - Commission | Total Commission
------------------|----------------|--------------|------------------------|------------------------------|-------------------------------|-----------------------------------|------------------
John Doe          | INV/001        | 2025-01-15   | ₹1500.00               | ₹150.00                     | ₹1800.00                      | ₹180.00                         | ₹330.00
Jane Smith        | INV/002        | 2025-01-16   | ₹1500.00               | ₹150.00                     | ₹0.00                         | ₹0.00                           | ₹150.00
TOTALS            |                |              | ₹3000.00               | ₹300.00                     | ₹1800.00                      | ₹180.00                         | ₹480.00
```

## How It Works

### 1. Data Collection
- Searches for medical appointments within the specified date range
- Filters appointments by state (excludes cancelled)
- Collects all related invoices (draft or posted)

### 2. Therapy Data Processing
- Groups invoice lines by therapy type
- Calculates total value and commission for each therapy
- Commission is calculated based on therapy type configuration:
  - **Fixed Amount**: Direct commission value
  - **Percentage**: Commission as percentage of total value

### 3. Excel Generation
- Creates dynamic columns based on available therapy types
- Applies professional formatting (colors, borders, number formats)
- Includes summary totals and report metadata

## Usage

### 1. Access the Report
- Navigate to: **Healthcare > Configuration > Therapy Report**
- Or search for "Therapy Report" in the apps menu

### 2. Configure Report Parameters
- **Start Date**: Beginning of the reporting period
- **End Date**: End of the reporting period
- **Therapy Types**: Leave empty for all types, or select specific ones

### 3. Generate Report
- Click "Generate & Download XLSX"
- The Excel file will automatically download

## Dependencies
- `basic_hms`: Core hospital management system
- `account`: Accounting module for invoice data

## Technical Details

### Models
- `therapy.report.wizard`: Transient model for report generation

### Key Methods
- `action_generate_xlsx_report()`: Main method for Excel generation

### Data Sources
- `medical.appointment`: Appointment records
- `account.move`: Invoice records
- `account.move.line`: Invoice line items with therapy data
- `therapy.type`: Therapy type configurations

## Commission Calculation

### Fixed Amount
```
Commission = therapy_type.commission_value
```

### Percentage
```
Commission = (line.price_subtotal × therapy_type.commission_value) ÷ 100
```

## Customization

### Adding New Therapy Types
1. Create new therapy type in `therapy.type` model
2. Configure commission type and value
3. Report will automatically include new columns

### Modifying Report Format
Edit the `action_generate_xlsx_report()` method in `therapy_report_wizard.py` to:
- Change column layouts
- Modify formatting styles
- Add new calculated fields
- Include additional data sources

## Troubleshooting

### Common Issues
1. **No data found**: Check date range and appointment states
2. **Empty therapy columns**: Verify therapy types are configured with products
3. **Commission not calculated**: Ensure invoice lines have `therapy_type_id` set

### Debug Mode
Enable debug logging to see detailed data processing:
```python
_logger.info(f"Processing invoice: {invoice.name}")
_logger.info(f"Therapy data: {therapy_data}")
```
