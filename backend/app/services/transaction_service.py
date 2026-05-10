from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone

from app.models import Transaction, User
from app.models.enums import TransactionStatus


def create_transaction(current_user, data, db: Session):
    borrower = db.query(User).filter(User.id == data.borrower_id).first()
    if not borrower:
        raise HTTPException(404, "Borrower not found")

    if borrower.id == current_user.id:
        raise HTTPException(400, "You cannot create a transaction with yourself")

    tx = Transaction(
        lender_id=current_user.id,
        borrower_id=data.borrower_id,
        amount=data.amount,
        transaction_type=data.transaction_type,
        description=data.description,
        due_date=data.due_date,
    )

    db.add(tx)
    db.commit()
    db.refresh(tx)

    return tx


def approve_transaction(tx_id: int, current_user, db: Session):
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()

    if not tx:
        raise HTTPException(404, "Transaction not found")

    if tx.borrower_id != current_user.id:
        raise HTTPException(403, "Only borrower can approve")

    if tx.status != TransactionStatus.pending:
        raise HTTPException(400, "Transaction not pending")

    tx.status = TransactionStatus.approved
    db.commit()

    return tx


def mark_as_paid(tx_id: int, current_user, db: Session):
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()

    if not tx:
        raise HTTPException(404, "Transaction not found")

    if tx.borrower_id != current_user.id:
        raise HTTPException(403, "Only borrower can mark as paid")

    if tx.status != TransactionStatus.approved:
        raise HTTPException(400, "Transaction not approved")

    tx.status = TransactionStatus.awaiting_confirmation
    db.commit()

    return tx


def confirm_payment(tx_id: int, current_user, db: Session):
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()

    if not tx:
        raise HTTPException(404, "Transaction not found")

    if tx.lender_id != current_user.id:
        raise HTTPException(403, "Only lender can confirm")

    if tx.status != TransactionStatus.awaiting_confirmation:
        raise HTTPException(400, "Not awaiting confirmation")

    tx.status = TransactionStatus.settled
    tx.settled_at = datetime.now(timezone.utc)

    db.commit()

    return tx