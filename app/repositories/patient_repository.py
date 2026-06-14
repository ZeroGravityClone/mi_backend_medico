from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate
from typing import List, Optional

class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Patient]:
        return self.db.query(Patient).offset(skip).limit(limit).all()

    def get_by_id(self, patient_id: int) -> Optional[Patient]:
        return self.db.query(Patient).filter(Patient.id == patient_id).first()

    def get_by_email(self, email: str) -> Optional[Patient]:
        return self.db.query(Patient).filter(Patient.email == email).first()

    def get_by_cedula(self, cedula: str) -> Optional[Patient]:
        return self.db.query(Patient).filter(Patient.cedula == cedula).first()

    def create(self, patient_in: PatientCreate) -> Patient:
        db_patient = Patient(
            first_name=patient_in.first_name,
            last_name=patient_in.last_name,
            cedula=patient_in.cedula,
            address=patient_in.address,
            birth_date=patient_in.birth_date,
            phone=patient_in.phone,
            email=patient_in.email,
            medical_history=patient_in.medical_history
        )
        self.db.add(db_patient)
        self.db.commit()
        self.db.refresh(db_patient)
        return db_patient

    def update(self, db_patient: Patient, patient_in: PatientUpdate) -> Patient:
        update_data = patient_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_patient, field, value)
        self.db.commit()
        self.db.refresh(db_patient)
        return db_patient

    def delete(self, db_patient: Patient) -> None:
        self.db.delete(db_patient)
        self.db.commit()