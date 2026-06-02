from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from app.repositories.patient_repository import PatientRepository
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User

router = APIRouter(prefix="/patients", tags=["patients"])

@router.get("/", response_model=List[PatientResponse])
def read_patients(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requiere Token válido
):
    """Lista todos los pacientes."""
    repo = PatientRepository(db)
    patients = repo.get_all(skip=skip, limit=limit)
    return patients

@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)  # Requiere Token y Rol ADMIN
):
    """Registra un nuevo paciente (Solo Administradores)."""
    repo = PatientRepository(db)
    
    if patient_in.email:
        existing = repo.get_by_email(patient_in.email)
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Ya existe un paciente con este correo electrónico."
            )
            
    return repo.create(patient_in)

@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    patient_in: PatientUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)  # Protegido para ADMIN
):
    """Actualiza la información de un paciente (Solo Administradores)."""
    repo = PatientRepository(db)
    db_patient = repo.get_by_id(patient_id)
    
    if not db_patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")
        
    return repo.update(db_patient=db_patient, patient_in=patient_in)

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)  # Protegido para ADMIN
):
    """Elimina un paciente del sistema (Solo Administradores)."""
    repo = PatientRepository(db)
    db_patient = repo.get_by_id(patient_id)
    
    if not db_patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")
        
    repo.delete(db_patient=db_patient)