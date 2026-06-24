from sqlalchemy.orm import Session
from app.models.patient import Loan
from app.schemas.loan import LoanCreate
from datetime import date
from typing import List, Optional

class LoanRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_loans(self) -> List[Loan]:
        return self.db.query(Loan).order_by(Loan.id.desc()).all()

    def create_loan(self, loan_in: LoanCreate) -> Loan:
        db_loan = Loan(
            patient_id=loan_in.patient_id,
            borrower_name=loan_in.borrower_name,
            checkout_date=loan_in.checkout_date,
            expected_return_date=loan_in.expected_return_date,
            status="ACTIVO"
        )
        self.db.add(db_loan)
        self.db.commit()
        self.db.refresh(db_loan)
        return db_loan

    def mark_as_returned(self, loan_id: int) -> Optional[Loan]:
        loan = self.db.query(Loan).filter(Loan.id == loan_id).first()
        if loan:
            # Usamos setattr para contentar al tipado estricto de Pylance
            setattr(loan, "status", "DEVUELTO")
            setattr(loan, "actual_return_date", date.today())
            self.db.commit()
            self.db.refresh(loan)
        return loan