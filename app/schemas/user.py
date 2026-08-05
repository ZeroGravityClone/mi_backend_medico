from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class UserBase(BaseModel):
    username: str
    permissions: Optional[Dict[str, Any]] = None

class UserCreate(UserBase):
    password: str
    role: Optional[str] = "GUEST"

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True