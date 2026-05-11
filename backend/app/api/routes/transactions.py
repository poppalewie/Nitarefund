from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.schemas.transaction import TransactionCreate, TransactionOut
from app.services import transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionOut)
def create(data: TransactionCreate,
           db: Session = Depends(get_db),
           current_user = Depends(get_current_user)):
    return transaction_service.create_transaction(current_user, data, db)


@router.post("/{tx_id}/approve")
def approve(tx_id: int,
            db: Session = Depends(get_db),
            current_user = Depends(get_current_user)):
    return transaction_service.approve_transaction(tx_id, current_user, db)


@router.post("/{tx_id}/pay")
def pay(tx_id: int,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)):
    return transaction_service.mark_as_paid(tx_id, current_user, db)


@router.post("/{tx_id}/confirm")
def confirm(tx_id: int,
            db: Session = Depends(get_db),
            current_user = Depends(get_current_user)):
    return transaction_service.confirm_payment(tx_id, current_user, db)

@router.post("/{tx_id}/cancel")
def cancel(tx_id: int,
           db: Session = Depends(get_db),
           current_user = Depends(get_current_user)):
    return transaction_service.cancel_transaction(tx_id, current_user, db)

@router.post("/{tx_id}/dispute")
def dispute(tx_id: int,
            db: Session = Depends(get_db),
            current_user = Depends(get_current_user)):
    return transaction_service.dispute_transaction(tx_id, current_user, db)