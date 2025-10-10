"""
DMT service layer for business logic
"""
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.schemas import DMTRecordCreate, DMTRecordUpdate
import logging

logger = logging.getLogger(__name__)


class DMTService:
    """Service for DMT-related operations"""
    
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def _generate_report_number(self) -> str:
        """Generate next report number starting from 1000"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT report_number FROM dmt_records 
                WHERE report_number LIKE 'RPT-%'
                ORDER BY id DESC LIMIT 1
            """)
            row = cursor.fetchone()
            
            if row and row[0]:
                # Extract number from RPT-XXXX format
                try:
                    last_num = int(row[0].split('-')[1])
                    next_num = last_num + 1
                except (IndexError, ValueError):
                    next_num = 1000
            else:
                next_num = 1000
            
            return f"RPT-{next_num:04d}"
        except sqlite3.Error as e:
            logger.error(f"Error generating report number: {e}")
            return f"RPT-1000"
    
    def get_record_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Get DMT record by ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT d.*, 
                       u1.username as created_by_username,
                       u2.username as assigned_to_username
                FROM dmt_records d
                LEFT JOIN users u1 ON d.created_by_user_id = u1.id
                LEFT JOIN users u2 ON d.assigned_to_user_id = u2.id
                WHERE d.id = ?
            """, (record_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_dict(row, cursor.description)
            return None
        except sqlite3.Error as e:
            logger.error(f"Database error getting DMT record {record_id}: {e}")
            raise
    
    def get_records_for_user(self, user_id: int, user_role: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get DMT records based on user role and permissions"""
        try:
            cursor = self.conn.cursor()
            
            # Admins and Supervisors see all records
            if user_role in ['Admin', 'Supervisor']:
                cursor.execute("""
                    SELECT d.*, 
                           u1.username as created_by_username,
                           u2.username as assigned_to_username
                    FROM dmt_records d
                    LEFT JOIN users u1 ON d.created_by_user_id = u1.id
                    LEFT JOIN users u2 ON d.assigned_to_user_id = u2.id
                    ORDER BY d.created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, skip))
            else:
                # Others see only their own records or assigned records
                cursor.execute("""
                    SELECT d.*, 
                           u1.username as created_by_username,
                           u2.username as assigned_to_username
                    FROM dmt_records d
                    LEFT JOIN users u1 ON d.created_by_user_id = u1.id
                    LEFT JOIN users u2 ON d.assigned_to_user_id = u2.id
                    WHERE d.created_by_user_id = ? OR d.assigned_to_user_id = ?
                    ORDER BY d.created_at DESC
                    LIMIT ? OFFSET ?
                """, (user_id, user_id, limit, skip))
            
            records = []
            for row in cursor.fetchall():
                records.append(self._row_to_dict(row, cursor.description))
            
            return records
        except sqlite3.Error as e:
            logger.error(f"Database error getting DMT records for user {user_id}: {e}")
            raise
    
    def create_record(self, record_data: DMTRecordCreate, created_by_user_id: int) -> Dict[str, Any]:
        """Create a new DMT record"""
        try:
            report_number = self._generate_report_number()
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO dmt_records (
                    report_number, date, shift, area, part_number, customer,
                    car_type, quantity_inspected, quantity_defective, disposition,
                    failure_code, description, created_by_user_id, assigned_to_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_number,
                record_data.date,
                record_data.shift,
                record_data.area,
                record_data.part_number,
                record_data.customer,
                record_data.car_type,
                record_data.quantity_inspected,
                record_data.quantity_defective,
                record_data.disposition,
                record_data.failure_code,
                record_data.description,
                created_by_user_id,
                record_data.assigned_to_user_id
            ))
            
            self.conn.commit()
            record_id = cursor.lastrowid
            
            logger.info(f"DMT record created: {report_number} (ID: {record_id})")
            return self.get_record_by_id(record_id)
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Database error creating DMT record: {e}")
            raise
    
    def update_record(self, record_id: int, record_data: DMTRecordUpdate, user_id: int, user_role: str) -> Optional[Dict[str, Any]]:
        """Update an existing DMT record"""
        try:
            record = self.get_record_by_id(record_id)
            if not record:
                return None
            
            # Check permissions
            if user_role not in ['Admin', 'Supervisor']:
                if record['created_by_user_id'] != user_id and record['assigned_to_user_id'] != user_id:
                    raise PermissionError("You don't have permission to edit this record")
            
            cursor = self.conn.cursor()
            update_fields = []
            params = []
            
            for field in ['date', 'shift', 'area', 'part_number', 'customer', 'car_type',
                         'quantity_inspected', 'quantity_defective', 'disposition',
                         'failure_code', 'description', 'assigned_to_user_id']:
                value = getattr(record_data, field, None)
                if value is not None:
                    update_fields.append(f"{field} = ?")
                    params.append(value)
            
            if not update_fields:
                return record
            
            params.append(record_id)
            query = f"UPDATE dmt_records SET {', '.join(update_fields)} WHERE id = ?"
            
            cursor.execute(query, params)
            self.conn.commit()
            
            logger.info(f"DMT record updated: ID {record_id}")
            return self.get_record_by_id(record_id)
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Database error updating DMT record {record_id}: {e}")
            raise
    
    def delete_record(self, record_id: int, user_id: int, user_role: str) -> bool:
        """Delete a DMT record"""
        try:
            record = self.get_record_by_id(record_id)
            if not record:
                return False
            
            # Check permissions
            if user_role not in ['Admin', 'Supervisor']:
                if record['created_by_user_id'] != user_id:
                    raise PermissionError("You don't have permission to delete this record")
            
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM dmt_records WHERE id = ?", (record_id,))
            self.conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"DMT record deleted: ID {record_id}")
            return deleted
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Database error deleting DMT record {record_id}: {e}")
            raise
    
    def _row_to_dict(self, row, description) -> Dict[str, Any]:
        """Convert database row to dictionary"""
        return {desc[0]: row[i] for i, desc in enumerate(description)}
