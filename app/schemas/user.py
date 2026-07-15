from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str  # Cambiado de email (EmailStr) a texto plano (str)

class UserCreate(UserBase):
    password: str
    role: Optional[str] = "GUEST"

class UserResponse(UserBase):
    id: int
    is_active: bool
    role: str  # <-- LÍNEA AGREGADA: Esto permite que FastAPI envíe el rol a React [1.1]
    created_at: datetime

    class Config:
        from_attributes = True