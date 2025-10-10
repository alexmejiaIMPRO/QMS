"""
Authentication utilities and user management
"""
import hashlib
import secrets
import uuid
import sqlite3
from enum import Enum
from typing import Optional
from fastapi import Request, HTTPException, status
from database.connection import get_db


class UserRole(str, Enum):
    """User roles in the system"""
    ADMIN = "Admin"
    SUPERVISOR = "Supervisor"
    INSPECTOR = "Inspector"
    ENGINEER = "Engineer"
    MANAGER = "Manager"
    OPERATOR = "Operator"


ROLE_HIERARCHY = {
    "Admin": 5,
    "Inspector": 5,  # Same level as Admin for DMT permissions
    "Manager": 4,
    "Engineer": 3,
    "Supervisor": 2,
    "Operator": 1
}


def get_assignable_users(current_user_role: str) -> list:
    """
    Get users that can be assigned to based on role hierarchy.
    Users can only assign to roles equal or higher than their own.
    """
    try:
        current_role_level = ROLE_HIERARCHY.get(current_user_role, 0)
        
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()
        
        c.execute("""
            SELECT id, username, role, is_active
            FROM users
            WHERE is_active = 1
            ORDER BY username
        """)
        
        all_users = [dict(row) for row in c.fetchall()]
        conn.close()
        
        # Filter users based on role hierarchy
        assignable_users = [
            user for user in all_users
            if ROLE_HIERARCHY.get(user["role"], 0) >= current_role_level
        ]
        
        return assignable_users
    except Exception as e:
        print(f"Error getting assignable users: {e}")
        return []


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${pwd_hash}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    try:
        salt, pwd_hash = password_hash.split("$")
        return hashlib.sha256((password + salt).encode()).hexdigest() == pwd_hash
    except (ValueError, AttributeError) as e:
        print(f"Error verifying password: {e}")
        return False


def create_user(username: str, password: str, role: UserRole) -> dict:
    """Create a new user"""
    if not username or not password:
        raise ValueError("Username and password are required")
    
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long")
    
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()
    
    user_id = str(uuid.uuid4())
    password_hash = hash_password(password)
    
    try:
        c.execute("""
            INSERT INTO users (id, username, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, password_hash, role.value))
        conn.commit()
        
        return {
            "id": user_id,
            "username": username,
            "role": role.value
        }
    except sqlite3.IntegrityError:
        raise ValueError("Username already exists")
    except Exception as e:
        print(f"Error creating user: {e}")
        raise ValueError(f"Failed to create user: {str(e)}")
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate a user and return user data if successful"""
    if not username or not password:
        return None
    
    try:
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()
        
        c.execute("""
            SELECT id, username, password_hash, role, is_active
            FROM users
            WHERE username = ? AND is_active = 1
        """, (username,))
        
        user = c.fetchone()
        conn.close()
        
        if user and verify_password(password, user["password_hash"]):
            return {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"]
            }
        return None
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None


def get_current_user(request: Request) -> Optional[dict]:
    """Get the current logged-in user from session"""
    return request.session.get("user")


def require_admin(request: Request) -> dict:
    """Require admin role for the current user"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    if user["role"] != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


def create_default_admin():
    """Create default admin user if no users exist"""
    try:
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) as count FROM users")
        count = c.fetchone()["count"]
        conn.close()
        
        if count == 0:
            create_user("admin", "admin123", UserRole.ADMIN)
            print("✅ Default admin user created (username: admin, password: admin123)")
    except Exception as e:
        print(f"⚠️  Warning: Could not create default admin user: {e}")


def get_all_users():
    """Get all users"""
    try:
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()
        
        c.execute("""
            SELECT id, username, role, is_active, created_at, updated_at
            FROM users
            ORDER BY created_at DESC
        """)
        
        users = [dict(row) for row in c.fetchall()]
        conn.close()
        return users
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []


def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get a user by ID"""
    if not user_id:
        return None
    
    try:
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()
        
        c.execute("""
            SELECT id, username, role, is_active, created_at, updated_at
            FROM users
            WHERE id = ?
        """, (user_id,))
        
        user = c.fetchone()
        conn.close()
        
        return dict(user) if user else None
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None


def update_user(user_id: str, username: str = None, password: str = None, role: UserRole = None) -> bool:
    """Update a user"""
    if not user_id:
        return False
    
    if password and len(password) < 6:
        raise ValueError("Password must be at least 6 characters long")
    
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()
    
    updates = []
    params = []
    
    if username:
        updates.append("username = ?")
        params.append(username)
    
    if password:
        updates.append("password_hash = ?")
        params.append(hash_password(password))
    
    if role:
        updates.append("role = ?")
        params.append(role.value)
    
    if not updates:
        conn.close()
        return False
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(user_id)
    
    try:
        c.execute(f"""
            UPDATE users
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        conn.commit()
        success = c.rowcount > 0
    except sqlite3.IntegrityError:
        print(f"Error: Username already exists")
        success = False
    except Exception as e:
        print(f"Error updating user: {e}")
        success = False
    finally:
        conn.close()
    
    return success


def delete_user(user_id: str) -> bool:
    """Delete a user (soft delete)"""
    if not user_id:
        return False
    
    try:
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()
        
        c.execute("""
            UPDATE users
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))
        
        conn.commit()
        success = c.rowcount > 0
        conn.close()
        
        return success
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False


def activate_user(user_id: str) -> bool:
    """Activate a user"""
    if not user_id:
        return False
    
    try:
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()
        
        c.execute("""
            UPDATE users
            SET is_active = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))
        
        conn.commit()
        success = c.rowcount > 0
        conn.close()
        
        return success
    except Exception as e:
        print(f"Error activating user: {e}")
        return False
