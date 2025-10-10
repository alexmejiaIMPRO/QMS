"""
Database connection and initialization
"""
import sqlite3
import os
from config import Config, EntityType


class Database:
    """Database connection and initialization handler"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        db_exists = os.path.exists(db_path)
        if not db_exists:
            print(f"Creating new database at {db_path}")
        self.init_db()

    def get_connection(self):
        """Get a database connection with row factory"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.DatabaseError as e:
            print(f"Database error: {e}")
            print(f"The database file may be corrupted. Please delete {self.db_path} and run scripts/seed_database.py")
            raise

    def init_db(self):
        """Initialize database tables and indexes"""
        try:
            conn = self.get_connection()
            c = conn.cursor()

            # Create entity tables
            for entity in EntityType:
                c.execute(f"""
                    CREATE TABLE IF NOT EXISTS {entity.value} (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)
                c.execute(
                    f"CREATE INDEX IF NOT EXISTS idx_{entity.value}_name ON {entity.value}(name)"
                )
                c.execute(
                    f"CREATE INDEX IF NOT EXISTS idx_{entity.value}_created ON {entity.value}(created_at)"
                )

            c.execute("""
                CREATE TABLE IF NOT EXISTS dmt_records (
                    id TEXT PRIMARY KEY,
                    report_number INTEGER UNIQUE,
                    -- General Information
                    work_center TEXT,
                    part_num TEXT,
                    operation TEXT,
                    employee_name TEXT,
                    qty TEXT,
                    customer TEXT,
                    shop_order TEXT,
                    serial_number TEXT,
                    inspection_item TEXT,
                    date TEXT,
                    prepared_by TEXT,
                    -- Defect Description
                    description TEXT,
                    car_type TEXT,
                    car_cycle TEXT,
                    car_second_cycle_date TEXT,
                    -- Process Analysis
                    process_description TEXT,
                    analysis TEXT,
                    analysis_by TEXT,
                    -- Engineering
                    disposition TEXT,
                    disposition_date TEXT,
                    engineer TEXT,
                    failure_code TEXT,
                    rework_hours TEXT,
                    responsible_dept TEXT,
                    material_scrap_cost TEXT,
                    others_cost TEXT,
                    engineering_remarks TEXT,
                    repair_process TEXT,
                    -- Metadata
                    status TEXT DEFAULT 'open',
                    workflow_status TEXT DEFAULT 'draft',
                    supervisor_completed_at TIMESTAMP,
                    manager_completed_at TIMESTAMP,
                    engineer_completed_at TIMESTAMP,
                    created_by TEXT,
                    assigned_to TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    is_session BOOLEAN DEFAULT 0
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_dmt_records_id ON dmt_records(id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_dmt_records_report_number ON dmt_records(report_number)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_dmt_records_shop_order ON dmt_records(shop_order)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_dmt_records_part_num ON dmt_records(part_num)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_dmt_records_status ON dmt_records(status)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_dmt_records_created_by ON dmt_records(created_by)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_dmt_records_assigned_to ON dmt_records(assigned_to)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_dmt_records_is_session ON dmt_records(is_session)")

            c.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    user_id TEXT,
                    changes TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")

            c.execute("""
                CREATE TABLE IF NOT EXISTS report_counter (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    next_number INTEGER NOT NULL DEFAULT 1000
                )
            """)
            
            c.execute("INSERT OR IGNORE INTO report_counter (id, next_number) VALUES (1, 1000)")

            try:
                c.execute("SELECT workflow_status FROM dmt_records LIMIT 1")
            except sqlite3.OperationalError:
                c.execute("ALTER TABLE dmt_records ADD COLUMN workflow_status TEXT DEFAULT 'draft'")
                c.execute("ALTER TABLE dmt_records ADD COLUMN supervisor_completed_at TIMESTAMP")
                c.execute("ALTER TABLE dmt_records ADD COLUMN manager_completed_at TIMESTAMP")
                c.execute("ALTER TABLE dmt_records ADD COLUMN engineer_completed_at TIMESTAMP")
                print("Added workflow columns to dmt_records table")

            try:
                c.execute("SELECT employee_number FROM employees LIMIT 1")
            except sqlite3.OperationalError:
                c.execute("ALTER TABLE employees ADD COLUMN employee_number TEXT")
                c.execute("CREATE INDEX IF NOT EXISTS idx_employees_number ON employees(employee_number)")
                print("Added employee_number column to employees table")

            try:
                c.execute("SELECT is_session FROM dmt_records LIMIT 1")
            except sqlite3.OperationalError:
                c.execute("ALTER TABLE dmt_records ADD COLUMN is_session BOOLEAN DEFAULT 0")
                c.execute("CREATE INDEX IF NOT EXISTS idx_dmt_records_is_session ON dmt_records(is_session)")
                print("Added is_session column to dmt_records table")

            conn.commit()
            conn.close()
        except sqlite3.DatabaseError as e:
            print(f"\n{'='*60}")
            print("DATABASE ERROR DETECTED")
            print(f"{'='*60}")
            print(f"Error: {e}")
            print(f"\nThe database file '{self.db_path}' appears to be corrupted.")
            print("\nTo fix this issue:")
            print(f"1. Delete the corrupted database: rm {self.db_path}")
            print("2. Run the seed script: python scripts/seed_database.py")
            print(f"{'='*60}\n")
            raise

try:
    db = Database(Config.DATABASE_PATH)
except sqlite3.DatabaseError:
    print("\nPlease fix the database issue before starting the application.")
    import sys
    sys.exit(1)


def get_db():
    """Get the global database instance"""
    return db
