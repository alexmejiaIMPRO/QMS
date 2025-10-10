# CSV Import Format Guide

This guide explains the required CSV format for bulk importing data into the Quality Management System.

## General Rules

- **File Format**: UTF-8 encoded CSV files
- **Headers**: First row must contain column headers (case-sensitive)
- **Empty Rows**: Empty rows will be skipped
- **Duplicates**: Items with duplicate names will be skipped automatically
- **Validation**: All required fields must be filled

---

## Employees

### Required Columns
- `name` - Employee full name
- `employee_number` - Unique employee identifier (e.g., EMP-1001)

### Example CSV

\`\`\`csv
name,employee_number
John Smith,EMP-1001
Maria Garcia,EMP-1002
David Chen,EMP-1003
Sarah Johnson,EMP-1004
\`\`\`

### Notes
- Employee numbers should be unique
- Recommended format: EMP-XXXX (e.g., EMP-1001, EMP-1002)
- Names can include spaces and special characters

---

## Work Centers

### Required Columns
- `name` - Work center name

### Example CSV

\`\`\`csv
name
Assembly Line 1
Quality Control Station
Packaging Department
Shipping Dock
Machining Center A
\`\`\`

### Notes
- Work center names should be descriptive
- Can include numbers and special characters

---

## Part Numbers

### Required Columns
- `name` - Part number or identifier

### Example CSV

\`\`\`csv
name
PN-12345
PN-67890
PART-ABC-001
COMPONENT-XYZ-500
SKU-9876
\`\`\`

### Notes
- Use your organization's part numbering convention
- Can include letters, numbers, and hyphens

---

## Operations

### Required Columns
- `name` - Operation name or code

### Example CSV

\`\`\`csv
name
Welding
Assembly
Inspection
Painting
Packaging
Quality Check
Final Testing
\`\`\`

### Notes
- Operation names should match your manufacturing processes
- Keep names consistent for reporting purposes

---

## Customers

### Required Columns
- `name` - Customer name

### Example CSV

\`\`\`csv
name
Acme Corporation
Global Industries Inc
TechStart Solutions
Manufacturing Partners LLC
Quality First Co
\`\`\`

### Notes
- Use official customer names
- Include legal entity suffixes (Inc, LLC, etc.) if applicable

---

## Inspection Items

### Required Columns
- `name` - Inspection item description

### Example CSV

\`\`\`csv
name
Dimensional Accuracy
Surface Finish
Weld Quality
Paint Adhesion
Electrical Continuity
Thread Inspection
Torque Verification
\`\`\`

### Notes
- Be specific about what is being inspected
- Use standardized terminology

---

## Failure Codes

### Required Columns
- `name` - Failure code and description

### Example CSV

\`\`\`csv
name
FC-001: Dimensional Out of Spec
FC-002: Surface Defect
FC-003: Material Defect
FC-004: Assembly Error
FC-005: Missing Component
FC-006: Incorrect Torque
\`\`\`

### Notes
- Include both code and description for clarity
- Use consistent numbering scheme

---

## Responsible Departments

### Required Columns
- `name` - Department name

### Example CSV

\`\`\`csv
name
Engineering
Quality Assurance
Production
Maintenance
Supply Chain
Purchasing
\`\`\`

### Notes
- Use official department names
- Keep names consistent across the system

---

## Import Process

1. **Prepare Your CSV File**
   - Use the templates above as a guide
   - Ensure UTF-8 encoding
   - Include all required columns

2. **Upload the File**
   - Navigate to the entity management page
   - Click "Choose File" in the Bulk Upload section
   - Select your CSV file
   - Click "Upload CSV"

3. **Review Results**
   - Success message shows number of items imported
   - Duplicate items are automatically skipped
   - Error messages indicate any issues found

4. **Troubleshooting**
   - **"Missing required column"**: Check that all required headers are present
   - **"File encoding error"**: Save your CSV as UTF-8
   - **"CSV parsing error"**: Check for malformed CSV (unclosed quotes, etc.)
   - **Items skipped**: These items already exist in the database

---

## Tips for Success

- **Start Small**: Test with a few rows before importing large files
- **Use Templates**: Export existing data to see the correct format
- **Check Encoding**: Always save as UTF-8 to avoid character issues
- **Validate Data**: Review your CSV in a text editor before uploading
- **Backup First**: Export existing data before large imports

---

## Example: Complete Employee Import

\`\`\`csv
name,employee_number
Alice Anderson,EMP-1001
Bob Brown,EMP-1002
Carol Chen,EMP-1003
David Davis,EMP-1004
Emma Evans,EMP-1005
Frank Foster,EMP-1006
Grace Green,EMP-1007
Henry Harris,EMP-1008
Iris Ivanov,EMP-1009
Jack Johnson,EMP-1010
\`\`\`

This file would import 10 employees with sequential employee numbers.

---

## Support

If you encounter issues not covered in this guide, please contact your system administrator.
\`\`\`

\`\`\`python file="" isHidden
