from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    cedula = Column(String(50), unique=True, index=True, nullable=False)
    address = Column(String(255), nullable=True)
    birth_date = Column(Date, nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    medical_history = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("PatientDocument", back_populates="patient", cascade="all, delete-orphan")


class PatientDocument(Base):
    __tablename__ = "patient_documents"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    
    # --- NUEVA METADATA DOCUMENTAL PROFESIONAL ---
    category = Column(String(100), nullable=False)       # Cédula, Contrato, etc.
    folder_number = Column(String(100), nullable=True)   # Ubicación física de la carpeta
    qr_code = Column(String(100), nullable=True)         # Código QR indexado
    document_status = Column(String(50), default="digitalizado", nullable=False) # digitalizado, validado, etc.
    
    # Auditoría: Quién subió el archivo (Relacionado con la tabla users)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True) 
    # ----------------------------------------------

    uploaded_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="documents")
    uploader = relationship("User")  # Relación para saber qué usuario del hospital lo procesó


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    borrower_name = Column(String(150), nullable=False) 
    checkout_date = Column(Date, nullable=False)        
    expected_return_date = Column(Date, nullable=False) 
    actual_return_date = Column(Date, nullable=True)    
    status = Column(String(50), default="ACTIVO", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient")