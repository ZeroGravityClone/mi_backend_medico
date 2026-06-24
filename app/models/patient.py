from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    cedula = Column(String, unique=True, index=True, nullable=True) # Usamos nullable=True para no romper registros viejos
    address = Column(String, nullable=True)
    birth_date = Column(Date, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    medical_history = Column(Text, nullable=True)  # Historial médico
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    # Vinculamos el préstamo al paciente/expediente
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    borrower_name = Column(String(150), nullable=False) # Ej. "Dra. Ramírez (Legal)"
    checkout_date = Column(Date, nullable=False)        # Fecha en que se lo llevó
    expected_return_date = Column(Date, nullable=False) # Fecha en que debe devolverlo
    actual_return_date = Column(Date, nullable=True)    # Fecha en que lo devolvió (Null si no lo ha devuelto)
    
    # Estatus: "ACTIVO", "DEVUELTO", "VENCIDO"
    status = Column(String(50), default="ACTIVO", nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relación inversa (Opcional, útil para consultas avanzadas)
    patient = relationship("Patient")