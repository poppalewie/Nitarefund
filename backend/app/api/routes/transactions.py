from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.schemas.transaction import TransactionCreate, TransactionOut
from app.services import transaction_service
from app.models import Transaction, User
from app.models.enums import TransactionStatus

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    uid     = current_user.id
    settled = [TransactionStatus.settled, TransactionStatus.auto_settled]

    total_lent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.lender_id == uid,
        Transaction.status.in_(settled)
    ).scalar() or 0

    total_borrowed = db.query(func.sum(Transaction.amount)).filter(
        Transaction.borrower_id == uid,
        Transaction.status.in_(settled)
    ).scalar() or 0

    pending_count = db.query(func.count(Transaction.id)).filter(
        or_(Transaction.lender_id == uid, Transaction.borrower_id == uid),
        Transaction.status.in_([
            TransactionStatus.pending,
            TransactionStatus.approved,
            TransactionStatus.awaiting_confirmation,
        ])
    ).scalar() or 0

    total_count = db.query(func.count(Transaction.id)).filter(
        or_(Transaction.lender_id == uid, Transaction.borrower_id == uid)
    ).scalar() or 0

    return {
        "total_lent":     float(total_lent),
        "total_borrowed": float(total_borrowed),
        "pending_count":  int(pending_count),
        "total_count":    int(total_count),
    }


@router.get("/", response_model=list[TransactionOut])
def get_my_transactions(
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    rows = (
        db.query(Transaction)
        .filter(
            or_(
                Transaction.lender_id == current_user.id,
                Transaction.borrower_id == current_user.id,
            )
        )
        .order_by(desc(Transaction.created_at))
        .limit(limit)
        .all()
    )

    user_ids = {r.lender_id for r in rows} | {r.borrower_id for r in rows}
    users    = {
        u.id: u.username
        for u in db.query(User).filter(User.id.in_(user_ids)).all()
    }

    return [
        TransactionOut(
            id=tx.id,
            lender_id=tx.lender_id,
            borrower_id=tx.borrower_id,
            lender_username=users.get(tx.lender_id),
            borrower_username=users.get(tx.borrower_id),
            amount=float(tx.amount),
            transaction_type=tx.transaction_type.value,
            description=tx.description,
            status=tx.status.value,
            due_date=tx.due_date,
            settled_at=tx.settled_at,
            created_at=tx.created_at,
        )
        for tx in rows
    ]


@router.post("/", response_model=TransactionOut)
def create(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return transaction_service.create_transaction(current_user, data, db)


@router.post("/{tx_id}/approve")
def approve(tx_id: int, db: Session = Depends(get_db),
            current_user = Depends(get_current_user)):
    return transaction_service.approve_transaction(tx_id, current_user, db)

@router.post("/{tx_id}/reject")
def reject(tx_id: int, db: Session = Depends(get_db),
           current_user = Depends(get_current_user)):
    """
    Lender hasn't received the payment — sends it back to pending.
    No trust penalty. Borrower can retry once the payment is actually made.
    """
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if tx.lender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the lender can reject a payment claim")
    if tx.status != TransactionStatus.awaiting_confirmation:
        raise HTTPException(status_code=400, detail="Can only reject payments awaiting confirmation")

    # Back to pending — borrower sees it and can re-approve and re-pay
    tx.status = TransactionStatus.pending
    db.commit()
    return tx


@router.post("/{tx_id}/pay")
def pay(tx_id: int, db: Session = Depends(get_db),
        current_user = Depends(get_current_user)):
    return transaction_service.mark_as_paid(tx_id, current_user, db)


@router.post("/{tx_id}/confirm")
def confirm(tx_id: int, db: Session = Depends(get_db),
            current_user = Depends(get_current_user)):
    return transaction_service.confirm_payment(tx_id, current_user, db)




@router.post("/{tx_id}/cancel")
def cancel(tx_id: int, db: Session = Depends(get_db),
           current_user = Depends(get_current_user)):
    return transaction_service.cancel_transaction(tx_id, current_user, db)


@router.post("/{tx_id}/dispute")
def dispute(tx_id: int, db: Session = Depends(get_db),
            current_user = Depends(get_current_user)):
    return transaction_service.dispute_transaction(tx_id, current_user, db)