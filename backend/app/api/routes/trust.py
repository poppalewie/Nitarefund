from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.services import trust_query_service
from app.models import TrustScore, Transaction
from app.models.enums import TransactionStatus

router = APIRouter(prefix="/trust", tags=["trust"])


@router.get("/me/network")
def my_network(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return trust_query_service.get_my_network(current_user.id, db)


@router.get("/pair/{user_id}")
def pair_trust(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return trust_query_service.get_pair_trust(current_user.id, user_id, db)


@router.get("/leaderboard")
def get_leaderboard(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    return trust_query_service.leaderboard(db, limit=limit)


@router.get("/me/history")
def trust_history(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    settled = [TransactionStatus.settled, TransactionStatus.auto_settled]

    rows = (
        db.query(
            func.date(Transaction.settled_at).label("date"),
            func.count(Transaction.id).label("count")
        )
        .filter(
            Transaction.borrower_id == current_user.id,
            Transaction.status.in_(settled),
            Transaction.settled_at.isnot(None)
        )
        .group_by(func.date(Transaction.settled_at))
        .order_by(func.date(Transaction.settled_at))
        .all()
    )

    current_score = db.query(
        func.coalesce(func.avg(TrustScore.score), 50.0)
    ).filter(TrustScore.user_b_id == current_user.id).scalar()
    current_score = round(float(current_score), 1)

    history = []
    running = 50.0
    total_txns = sum(r.count for r in rows) or 1

    for row in rows:
        weight  = row.count / total_txns
        running = running + (current_score - running) * weight
        history.append({
            "date":  str(row.date),
            "score": round(running, 1),
        })

    if history:
        history[-1]["score"] = current_score
    else:
        history = [{"date": "now", "score": current_score}]

    return history