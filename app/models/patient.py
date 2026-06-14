from sqlalchemy import Column, Integer, String, Text, Date, DateTime
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