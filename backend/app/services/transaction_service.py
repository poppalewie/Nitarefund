from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone

from app.models import Transaction, User
from app.models.enums import TransactionStatus
from app.services.wallet_service import get_balance, deduct, deposit
from app.services.trust_service import apply_event

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

    apply_event(
        a_id=tx.lender_id,
        b_id=tx.borrower_id,
        event="approve",
        db=db
    )

    return tx

THRESHOLD = 5000


def mark_as_paid(tx_id: int, current_user, db: Session):
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()

    if not tx:
        raise HTTPException(404, "Transaction not found")

    if tx.borrower_id != current_user.id:
        raise HTTPException(403, "Only borrower can pay")

    if tx.status != TransactionStatus.approved:
        raise HTTPException(400, "Transaction not approved")

    wallet_balance = get_balance(current_user.id, db)

    #AUTO-SETTLE PATH
    if wallet_balance >= THRESHOLD and wallet_balance >= float(tx.amount):
        deduct(current_user.id, float(tx.amount), db)

        tx.status = TransactionStatus.auto_settled
        tx.settled_at = datetime.now(timezone.utc)

        db.commit()

        apply_event(
            a_id=tx.lender_id,
            b_id=tx.borrower_id,
            event="auto_settle",
            db=db
        )

        # future: trigger notification
        return tx

    #NORMAL FLOW
    tx.status = TransactionStatus.awaiting_confirmation
    db.commit()

    tx.status = TransactionStatus.approved
    db.commit()

    apply_event(
        a_id=tx.lender_id,
        b_id=tx.borrower_id,
        event="pay",
        db=db
    )

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

    apply_event(
        a_id=tx.lender_id,
        b_id=tx.borrower_id,
        event="settle",
        db=db
    )


    return tx

def cancel_transaction(tx_id: int, current_user, db: Session):
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()

    if not tx:
        raise HTTPException(404, "Transaction not found")

    if tx.lender_id != current_user.id:
        raise HTTPException(403, "Only lender can cancel")

    if tx.status != TransactionStatus.pending:
        raise HTTPException(400, "Only pending transactions can be cancelled")

    tx.status = TransactionStatus.cancelled
    db.commit()

    apply_event(
        a_id=tx.borrower_id,   #  reversed
        b_id=tx.lender_id,
        event="cancel",
        db=db
    )

    return tx

def dispute_transaction(tx_id: int, current_user, db: Session):
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()

    if not tx:
        raise HTTPException(404, "Transaction not found")

    if tx.borrower_id != current_user.id:
        raise HTTPException(403, "Only borrower can dispute")

    if tx.status not in ["pending", "approved"]:
        raise HTTPException(400, "Cannot dispute at this stage")

    tx.status = TransactionStatus.disputed
    db.commit()

    apply_event(
        a_id=tx.lender_id,
        b_id=tx.borrower_id,
        event="dispute",
        db=db
    )


    return tx