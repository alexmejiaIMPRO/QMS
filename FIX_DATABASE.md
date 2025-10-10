# Fix Corrupted Database

If you see the error `sqlite3.DatabaseError: database disk image is malformed`, follow these steps:

## Step 1: Delete the Corrupted Database

\`\`\`bash
# Delete the corrupted database file
rm qms.db
\`\`\`

## Step 2: Run the Seed Script

The seed script will automatically create a fresh database with all tables and populate it with mock data:

\`\`\`bash
python scripts/seed_database.py
\`\`\`

This will create:
- **6 Users** with different roles (Admin, Engineer, Supervisor, Operator)
- **Mock data** for all entity tables (employees, work centers, customers, part numbers, etc.)
- **15 DMT Records** with various statuses and user assignments
- **Report numbering** starting at 1000

## Step 3: Start the Application

\`\`\`bash
uvicorn main:app --reload --host 0.0.0.0 --port 8080
\`\`\`

## Default Login Credentials

After seeding, you can login with these accounts:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| john_engineer | engineer123 | Engineer |
| sarah_supervisor | supervisor123 | Supervisor |
| mike_operator | operator123 | Operator |
| lisa_engineer | engineer123 | Engineer |
| tom_operator | operator123 | Operator |

## What Gets Created

### Users (6 total)
- 1 Admin
- 2 Engineers
- 1 Supervisor
- 2 Operators

### Entity Data
- 8 Employees
- 6 Work Centers
- 6 Customers
- 8 Part Numbers
- 6 Inspection Items
- 5 QC Inspectors
- 5 CAR Types
- 5 Dispositions
- 6 Failure Codes
- 5 Areas
- 4 Levels
- 6 Calibration Equipment

### DMT Records (15 total)
- Various statuses (open, in_progress, closed)
- Assigned to different users
- Report numbers starting at 1000
- Complete with all fields populated

## Preventing Future Corruption

To avoid database corruption:
1. Always stop the server properly (Ctrl+C)
2. Don't manually edit the database file
3. Make regular backups: `cp qms.db qms.db.backup`
