from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional

class PatientBase(BaseModel):
    first_name: str
    last_name: str
    cedula: Optional[str] = None   
    address: Optional[str] = None
    cargo: Optional[str] = None  
    birth_date: date
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    medical_history: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    cedula: Optional[str] = None   
    address: Optional[str] = None
    cargo: Optional[str] = None  
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

class DocumentResponse(BaseModel):
    id: int
    patient_id: int
    file_name: str
    file_path: str
    category: str
    folder_number: Optional[str] = None
    qr_code: Optional[str] = None
    document_status: str
    uploaded_by: Optional[int] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True

class DocumentUpdate(BaseModel):
    file_name: Optional[str] = None
    category: Optional[str] = None
    folder_number: Optional[str] = None
    document_status: Optional[str] = None