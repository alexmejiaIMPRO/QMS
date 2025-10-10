"""
User service layer for business logic
"""
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
from auth.auth import hash_password, verify_password
from app.models.schemas import UserCreate, UserUpdate, UserRole
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related operations"""
    
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, username, email, full_name, role, is_active, created_at
                FROM users WHERE id = ?
            """, (user_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'full_name': row[3],
                    'role': row[4],
                    'is_active': row[5],
                    'created_at': row[6]
                }
            return None
        except sqlite3.Error as e:
            logger.error(f"Database error getting user by ID {user_id}: {e}")
            raise
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, username, password_hash, email, full_name, role, is_active, created_at
                FROM users WHERE username = ?
            """, (username,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'password_hash': row[2],
                    'email': row[3],
                    'full_name': row[4],
                    'role': row[5],
                    'is_active': row[6],
                    'created_at': row[7]
                }
            return None
        except sqlite3.Error as e:
            logger.error(f"Database error getting user by username {username}: {e}")
            raise
    
    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all users with pagination"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, username, email, full_name, role, is_active, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, skip))
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'full_name': row[3],
                    'role': row[4],
                    'is_active': row[5],
                    'created_at': row[6]
                })
            return users
        except sqlite3.Error as e:
            logger.error(f"Database error getting all users: {e}")
            raise
    
    def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create a new user"""
        try:
            # Check if username already exists
            existing_user = self.get_user_by_username(user_data.username)
            if existing_user:
                raise ValueError(f"Username '{user_data.username}' already exists")
            
            password_hash = hash_password(user_data.password)
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, full_name, role, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_data.username,
                password_hash,
                user_data.email,
                user_data.full_name,
                user_data.role.value,
                user_data.is_active
            ))
            
            self.conn.commit()
            user_id = cursor.lastrowid
            
            logger.info(f"User created: {user_data.username} (ID: {user_id})")
            return self.get_user_by_id(user_id)
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Database error creating user: {e}")
            raise
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[Dict[str, Any]]:
        """Update an existing user"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            cursor = self.conn.cursor()
            update_fields = []
            params = []
            
            if user_data.email is not None:
                update_fields.append("email = ?")
                params.append(user_data.email)
            
            if user_data.full_name is not None:
                update_fields.append("full_name = ?")
                params.append(user_data.full_name)
            
            if user_data.role is not None:
                update_fields.append("role = ?")
                params.append(user_data.role.value)
            
            if user_data.is_active is not None:
                update_fields.append("is_active = ?")
                params.append(user_data.is_active)
            
            if user_data.password is not None:
                update_fields.append("password_hash = ?")
                params.append(hash_password(user_data.password))
            
            if not update_fields:
                return user
            
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            
            cursor.execute(query, params)
            self.conn.commit()
            
            logger.info(f"User updated: ID {user_id}")
            return self.get_user_by_id(user_id)
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Database error updating user {user_id}: {e}")
            raise
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            self.conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"User deleted: ID {user_id}")
            return deleted
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Database error deleting user {user_id}: {e}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user"""
        try:
            user = self.get_user_by_username(username)
            
            if not user:
                logger.warning(f"Authentication failed: User not found - {username}")
                return None
            
            if not user.get('is_active'):
                logger.warning(f"Authentication failed: User inactive - {username}")
                return None
            
            if not verify_password(password, user['password_hash']):
                logger.warning(f"Authentication failed: Invalid password - {username}")
                return None
            
            # Remove password hash from response
            user.pop('password_hash', None)
            logger.info(f"User authenticated: {username}")
            return user
        except Exception as e:
            logger.error(f"Error authenticating user {username}: {e}")
            raise
