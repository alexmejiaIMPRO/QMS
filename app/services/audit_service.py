"""
Audit service layer for business logic
"""
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit log operations"""
    
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def log_action(self, user_id: Optional[int], action: str, entity_type: str, 
                   entity_id: Optional[int] = None, details: Optional[str] = None):
        """Log an audit action"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, action, entity_type, entity_id, details))
            self.conn.commit()
            logger.debug(f"Audit log created: {action} on {entity_type}")
        except sqlite3.Error as e:
            logger.error(f"Error creating audit log: {e}")
            # Don't raise - audit logging shouldn't break the main operation
    
    def get_logs(self, skip: int = 0, limit: int = 100, 
                 entity_type: Optional[str] = None,
                 user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get audit logs with optional filtering"""
        try:
            cursor = self.conn.cursor()
            
            query = """
                SELECT a.*, u.username
                FROM audit_logs a
                LEFT JOIN users u ON a.user_id = u.id
                WHERE 1=1
            """
            params = []
            
            if entity_type:
                query += " AND a.entity_type = ?"
                params.append(entity_type)
            
            if user_id:
                query += " AND a.user_id = ?"
                params.append(user_id)
            
            query += " ORDER BY a.timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, skip])
            
            cursor.execute(query, params)
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'id': row[0],
                    'user_id': row[1],
                    'action': row[2],
                    'entity_type': row[3],
                    'entity_id': row[4],
                    'details': row[5],
                    'timestamp': row[6],
                    'username': row[7] if len(row) > 7 else None
                })
            
            return logs
        except sqlite3.Error as e:
            logger.error(f"Database error getting audit logs: {e}")
            raise
