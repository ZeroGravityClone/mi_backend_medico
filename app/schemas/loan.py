from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class LoanBase(BaseModel):
    patient_id: int
    borrower_name: str
    checkout_date: date
    expected_return_date: date

class LoanCreate(LoanBase):
    pass

class LoanResponse(LoanBase):
    id: int
    actual_return_date: Optional[date] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True