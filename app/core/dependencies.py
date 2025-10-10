"""
Dependency injection for FastAPI
"""
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from database.connection import get_db_connection
from app.services.user_service import UserService
from app.services.dmt_service import DMTService
from app.services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)


def get_user_service(conn=Depends(get_db_connection)) -> UserService:
    """Get user service instance"""
    return UserService(conn)


def get_dmt_service(conn=Depends(get_db_connection)) -> DMTService:
    """Get DMT service instance"""
    return DMTService(conn)


def get_audit_service(conn=Depends(get_db_connection)) -> AuditService:
    """Get audit service instance"""
    return AuditService(conn)


def get_current_user(request: Request) -> Dict[str, Any]:
    """Get current authenticated user from session"""
    user = request.session.get('user')
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user


def get_current_active_user(current_user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current active user"""
    if not current_user.get('is_active'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_role(*allowed_roles: str):
    """Dependency to check if user has required role"""
    def role_checker(current_user: Dict = Depends(get_current_active_user)) -> Dict[str, Any]:
        user_role = current_user.get('role')
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, None otherwise"""
    return request.session.get('user')
