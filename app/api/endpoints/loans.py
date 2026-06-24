from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.loan import LoanCreate, LoanResponse
from app.repositories.loan_repository import LoanRepository
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/loans", tags=["loans"])

@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_loan(
    loan_in: LoanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = LoanRepository(db)
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