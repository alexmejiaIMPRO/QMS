"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles in the system"""
    ADMIN = "Admin"
    INSPECTOR = "Inspector"
    ENGINEER = "Engineer"
    SUPERVISOR = "Supervisor"
    MANAGER = "Manager"
    OPERATOR = "Operator"
    VIEWER = "Viewer"


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=6, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class DMTRecordBase(BaseModel):
    """Base DMT record schema"""
    report_number: Optional[str] = None
    date: Optional[str] = None
    shift: Optional[str] = None
    area: Optional[str] = None
    part_number: Optional[str] = None
    customer: Optional[str] = None
    car_type: Optional[str] = None
    quantity_inspected: Optional[int] = Field(None, ge=0)
    quantity_defective: Optional[int] = Field(None, ge=0)
    disposition: Optional[str] = None
    failure_code: Optional[str] = None
    description: Optional[str] = None
    assigned_to_user_id: Optional[int] = None


class DMTRecordCreate(DMTRecordBase):
    """Schema for creating DMT record"""
    pass


class DMTRecordUpdate(DMTRecordBase):
    """Schema for updating DMT record"""
    pass


class DMTRecordResponse(DMTRecordBase):
    """Schema for DMT record response"""
    id: int
    created_by_user_id: int
    created_by_username: Optional[str] = None
    assigned_to_username: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class EntityBase(BaseModel):
    """Base entity schema"""
    name: str = Field(..., min_length=1, max_length=200)


class EntityCreate(EntityBase):
    """Schema for creating entity"""
    pass


class EntityResponse(EntityBase):
    """Schema for entity response"""
    id: int
    
    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Schema for audit log response"""
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[int]
    details: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True
