"""
Configuration settings for the QMS application
"""

from enum import Enum
import os
from pathlib import Path


class Config:
    """Application configuration"""

    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "qms.db")

    # Pagination
    PAGE_SIZE: int = int(os.getenv("PAGE_SIZE", "20"))
    MAX_PAGE_SIZE: int = 100

    # Application
    APP_TITLE: str = "Quality Management System"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "Professional QMS with DMT tracking and user management"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    SESSION_COOKIE_NAME: str = "qms_session"
    SESSION_MAX_AGE: int = 3600 * 24  # 24 hours

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "qms.log")

    # Templates
    TEMPLATES_DIR: Path = Path("jinja_templates")
    STATIC_DIR: Path = Path("static")

    # CORS (if needed for API)
    CORS_ORIGINS: list = ["*"]

    @classmethod
    def validate(cls):
        """Validate configuration"""
        if cls.SECRET_KEY == "your-secret-key-change-in-production":
            import warnings

            warnings.warn("Using default SECRET_KEY. Change this in production!")


class EntityType(str, Enum):
    """Supported entity types in the system"""

    EMPLOYEES = "employees"
    LEVELS = "levels"
    AREAS = "areas"
    PARTNUMBERS = "partnumbers"
    CALIBRATIONS = "calibrations"
    WORKCENTERS = "workcenters"
    CUSTOMERS = "customers"
    INSPECTION_ITEMS = "inspection_items"
    PREPARED_BY = "prepared_by"
    CAR_TYPES = "car_types"
    DISPOSITIONS = "dispositions"
    FAILURE_CODES = "failure_codes"


class UserRole(str, Enum):
    """User roles with descriptions"""

    ADMIN = "Admin"
    ENGINEER = "Engineer"
    SUPERVISOR = "Supervisor"
    OPERATOR = "Operator"
    VIEWER = "Viewer"

    @classmethod
    def get_permissions(cls, role: str) -> dict:
        """Get permissions for a role"""
        permissions = {
            cls.ADMIN: {
                "can_manage_users": True,
                "can_manage_entities": True,
                "can_view_all_dmt": True,
                "can_edit_all_dmt": True,
                "can_delete_dmt": True,
                "can_view_audit_logs": True,
            },
            cls.SUPERVISOR: {
                "can_manage_users": False,
                "can_manage_entities": True,
                "can_view_all_dmt": True,
                "can_edit_all_dmt": True,
                "can_delete_dmt": True,
                "can_view_audit_logs": True,
            },
            cls.ENGINEER: {
                "can_manage_users": False,
                "can_manage_entities": False,
                "can_view_all_dmt": False,
                "can_edit_all_dmt": False,
                "can_delete_dmt": False,
                "can_view_audit_logs": False,
            },
            cls.OPERATOR: {
                "can_manage_users": False,
                "can_manage_entities": False,
                "can_view_all_dmt": False,
                "can_edit_all_dmt": False,
                "can_delete_dmt": False,
                "can_view_audit_logs": False,
            },
            cls.VIEWER: {
                "can_manage_users": False,
                "can_manage_entities": False,
                "can_view_all_dmt": False,
                "can_edit_all_dmt": False,
                "can_delete_dmt": False,
                "can_view_audit_logs": False,
            },
        }
        return permissions.get(role, permissions.get(cls.VIEWER.value, {}))
