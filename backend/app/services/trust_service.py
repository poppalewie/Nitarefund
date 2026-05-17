from sqlalchemy.orm import Session
from app.models import TrustScore, Transaction
from app.models.enums import TransactionStatus
from fastapi import HTTPException

MIN_SCORE = 0
MAX_SCORE = 100
BASE_SCORE = 50

WEIGHTS = {
    "approve":          2,
    "pay":              0,
    "auto_settle":     10,
    "settle":          12,
    "dispute":         -4,   # lender's trust of borrower drops
    "dispute_counter": -3,   # borrower's trust of lender drops (mutual cost)
    "cancel":          -2,
}

def _clamp(value: float) -> float:
    return max(MIN_SCORE, min(MAX_SCORE, value))


def get_or_create_pair(a_id: int, b_id: int, db: Session) -> TrustScore:
    ts = (
        db.query(TrustScore)
        .filter(TrustScore.user_a_id == a_id, TrustScore.user_b_id == b_id)
        .first()
    )
    if not ts:
        ts = TrustScore(user_a_id=a_id, user_b_id=b_id, score=BASE_SCORE)
        db.add(ts)
        db.commit()
        db.refresh(ts)
    return ts


def _reciprocity_factor(user_id: int, db: Session) -> float:
    """
    Measures how much a user lends vs borrows.
    0.7 → mostly borrower
    1.0 → balanced
    1.2 → strong lender
    """
    total_lent = (
        db.query(Transaction)
        .filter(Transaction.lender_id == user_id, Transaction.status.in_([
            TransactionStatus.settled, TransactionStatus.auto_settled
        ]))
        .count()
    )

    total_borrowed = (
        db.query(Transaction)
        .filter(Transaction.borrower_id == user_id, Transaction.status.in_([
            TransactionStatus.settled, TransactionStatus.auto_settled
        ]))
        .count()
    )

    ratio = total_lent / (total_borrowed + 1)

    if ratio < 0.5:
        return 0.8
    elif ratio > 1.5:
        return 1.2
    return 1.0


def apply_event(a_id: int, b_id: int, event: str, db: Session):
    """
    Update trust A → B based on an event performed by B (from A’s perspective).
    Example: borrower B pays lender A → update trust A→B positively.
    """
    if event not in WEIGHTS:
        raise HTTPException(400, f"Unknown trust event: {event}")

    ts = get_or_create_pair(a_id, b_id, db)

    base_delta = WEIGHTS[event]

    # Apply reciprocity based on B (the actor)
    factor = _reciprocity_factor(b_id, db)
    delta = base_delta * factor

    ts.score = _clamp(float(ts.score) + delta)

    db.commit()
    db.refresh(ts)

    return ts