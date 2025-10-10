"""
Authentication module
"""
from .auth import (
    hash_password,
    verify_password,
    create_user,
    authenticate_user,
    get_current_user,
    require_admin,
    UserRole
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_user",
    "authenticate_user",
    "get_current_user",
    "require_admin",
    "UserRole"
]
