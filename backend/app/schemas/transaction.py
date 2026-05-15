from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.enums import TransactionType


class TransactionCreate(BaseModel):
    borrower_id: int
    amount: float = Field(gt=0)
    transaction_type: TransactionType = TransactionType.monetary
    description: Optional[str] = None
    due_date: Optional[datetime] = None


class TransactionOut(BaseModel):
    id: int
    lender_id: int
    borrower_id: int
    lender_username: Optional[str] = None
    borrower_username: Optional[str] = None
    amount: float
    transaction_type: str
    description: Optional[str] = None
    status: str
    due_date: Optional[datetime] = None
    settled_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True