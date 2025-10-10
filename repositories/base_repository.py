"""
Base repository for CRUD operations
"""
import json
import uuid
from typing import Optional, Tuple, List, Dict
from datetime import datetime, timedelta
from config import Config, EntityType
from database import get_db


class Repository:
    """Generic repository for entity CRUD operations"""
    
    def __init__(self, entity_type: EntityType):
        self.entity_type = entity_type
        self.table = entity_type.value
        self.db = get_db()

    def get_all(
        self, 
        days: Optional[int] = None, 
        page: int = 1, 
        search: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """Get all items with optional filtering and pagination"""
        conn = self.db.get_connection()
        c = conn.cursor()

        query = f"SELECT * FROM {self.table} WHERE is_active = 1"
        params = []

        if days:
            date_filter = datetime.now() - timedelta(days=days)
            query += " AND created_at >= ?"
            params.append(date_filter)

        if search:
            query += " AND name LIKE ?"
            params.append(f"%{search}%")

        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        c.execute(count_query, params)
        total = c.fetchone()[0]

        # Get paginated results
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([Config.PAGE_SIZE, (page - 1) * Config.PAGE_SIZE])

        c.execute(query, params)
        items = [dict(row) for row in c.fetchall()]
        conn.close()

        return items, total

    def get_by_id(self, item_id: str) -> Optional[Dict]:
        """Get a single item by ID"""
        conn = self.db.get_connection()
        c = conn.cursor()
        c.execute(
            f"SELECT * FROM {self.table} WHERE id = ? AND is_active = 1", 
            (item_id,)
        )
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    def create(self, name: str, employee_number: Optional[str] = None) -> Dict:
        """Create a new item"""
        conn = self.db.get_connection()
        c = conn.cursor()

        item_id = str(uuid.uuid4())[:8]
        
        if self.entity_type == EntityType.EMPLOYEES and employee_number:
            c.execute(
                f"INSERT INTO {self.table} (id, name, employee_number) VALUES (?, ?, ?)", 
                (item_id, name, employee_number)
            )
            changes = {"name": name, "employee_number": employee_number}
        else:
            c.execute(
                f"INSERT INTO {self.table} (id, name) VALUES (?, ?)", 
                (item_id, name)
            )
            changes = {"name": name}
        
        # Log the creation
        c.execute(
            "INSERT INTO audit_log (entity_type, entity_id, action, changes) VALUES (?, ?, ?, ?)",
            (self.entity_type.value, item_id, "CREATE", json.dumps(changes)),
        )

        conn.commit()
        c.execute(f"SELECT * FROM {self.table} WHERE id = ?", (item_id,))
        new_item = dict(c.fetchone())
        conn.close()

        return new_item

    def update(self, item_id: str, name: str, employee_number: Optional[str] = None) -> Optional[Dict]:
        """Update an existing item"""
        conn = self.db.get_connection()
        c = conn.cursor()

        # Get old value for audit log
        c.execute(f"SELECT * FROM {self.table} WHERE id = ?", (item_id,))
        old_item = c.fetchone()
        if not old_item:
            conn.close()
            return None

        old_item = dict(old_item)

        if self.entity_type == EntityType.EMPLOYEES and employee_number is not None:
            c.execute(
                f"UPDATE {self.table} SET name = ?, employee_number = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (name, employee_number, item_id),
            )
            changes = {
                "old": {"name": old_item["name"], "employee_number": old_item.get("employee_number")},
                "new": {"name": name, "employee_number": employee_number}
            }
        else:
            c.execute(
                f"UPDATE {self.table} SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (name, item_id),
            )
            changes = {"old": old_item["name"], "new": name}
        
        # Log the update
        c.execute(
            "INSERT INTO audit_log (entity_type, entity_id, action, changes) VALUES (?, ?, ?, ?)",
            (
                self.entity_type.value,
                item_id,
                "UPDATE",
                json.dumps(changes),
            ),
        )

        conn.commit()
        c.execute(f"SELECT * FROM {self.table} WHERE id = ?", (item_id,))
        updated_item = dict(c.fetchone())
        conn.close()

        return updated_item

    def delete(self, item_id: str) -> bool:
        """Soft delete an item"""
        conn = self.db.get_connection()
        c = conn.cursor()

        c.execute(
            f"UPDATE {self.table} SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (item_id,),
        )
        affected = c.rowcount

        if affected > 0:
            c.execute(
                "INSERT INTO audit_log (entity_type, entity_id, action) VALUES (?, ?, ?)",
                (self.entity_type.value, item_id, "DELETE"),
            )

        conn.commit()
        conn.close()
        return affected > 0
