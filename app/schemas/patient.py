from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional

class PatientBase(BaseModel):
    first_name: str
    last_name: str
    cedula: Optional[str] = None   # <-- NUEVO
    address: Optional[str] = None  # <-- NUEVO
    birth_date: date
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    medical_history: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    cedula: Optional[str] = None   # <-- NUEVO
    address: Optional[str] = None  # <-- NUEVO
    birth_date: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    medical_history: Optional[str] = None

class PatientResponse(PatientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True