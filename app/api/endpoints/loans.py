from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.loan import LoanCreate, LoanResponse, LoanUpdate
from app.repositories.loan_repository import LoanRepository
from app.api.deps import get_current_user, get_current_admin  # <-- CORREGIDO: Importación agregada
from app.models.user import User
from app.models.patient import Loan  # <-- CORREGIDO: Importación agregada

router = APIRouter(prefix="/loans", tags=["loans"])

@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_loan(
    loan_in: LoanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registra la salida física de un expediente, validando previamente que no se encuentre ya afuera."""
    repo = LoanRepository(db)
    
    # 1. Validar si la carpeta física ya está prestada y fuera de la bóveda
    active_loan = repo.get_active_loan_by_patient(loan_in.patient_id)
    if active_loan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La carpeta física de este expediente ya se encuentra fuera de la bóveda. Solicitada por: {active_loan.borrower_name}."
        )
        
    return repo.create_loan(loan_in)

@router.get("/", response_model=List[LoanResponse])
def get_loans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = LoanRepository(db)
    return repo.get_all_loans()

@router.put("/{loan_id}/return", response_model=LoanResponse)
def return_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = LoanRepository(db)
    loan = repo.mark_as_returned(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    return loan

# MODIFICAR PRÉSTAMO HISTÓRICO (Solo ADMIN)
@router.put("/{loan_id}", response_model=LoanResponse)
def update_loan_record(
    loan_id: int,
    loan_in: LoanUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Permite al administrador modificar detalles de un préstamo de la bitácora."""
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Registro de préstamo no encontrado.")
        
    for field, value in loan_in.model_dump(exclude_unset=True).items():
        setattr(loan, field, value)
        
    db.commit()
    db.refresh(loan)
    return loan

# ELIMINAR PRÉSTAMO HISTÓRICO (Solo ADMIN)
@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan_record(
    loan_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Elimina permanentemente un registro de préstamo de la bitácora."""
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Registro de préstamo no encontrado.")
        
    db.delete(loan)
    db.commit()