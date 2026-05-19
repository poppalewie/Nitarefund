from sqlalchemy.orm import Session
from sqlalchemy import func, union
from app.models import TrustScore, User, Transaction


def get_pair_trust(a_id: int, b_id: int, db: Session) -> dict:
    """
    Returns the mutual trust score between two users.
    Raises 404 if they have never transacted — prevents random lookups.
    """
    from fastapi import HTTPException
    from sqlalchemy import or_
    from app.models import Transaction

    # Verify a real transaction relationship exists between the two users
    relationship = db.query(Transaction).filter(
        or_(
            (Transaction.lender_id == a_id) & (Transaction.borrower_id == b_id),
            (Transaction.lender_id == b_id) & (Transaction.borrower_id == a_id),
        )
    ).first()

    if not relationship:
        raise HTTPException(
            status_code=404,
            detail="This user is not in your network. You can only check trust scores with peers you have transacted with."
        )

    # Both directions
    ts_ab = db.query(TrustScore).filter(
        TrustScore.user_a_id == a_id,
        TrustScore.user_b_id == b_id
    ).first()

    ts_ba = db.query(TrustScore).filter(
        TrustScore.user_a_id == b_id,
        TrustScore.user_b_id == a_id
    ).first()

    scores = []
    if ts_ab: scores.append(float(ts_ab.score))
    if ts_ba: scores.append(float(ts_ba.score))

    # Peers exist but trust hasn't been computed yet (no settled transactions)
    if not scores:
        raise HTTPException(
            status_code=404,
            detail="No trust score yet — complete a transaction with this peer first."
        )

    avg = sum(scores) / len(scores)
    return {"score": round(avg, 1), "user_a_id": a_id, "user_b_id": b_id}

def get_my_network(user_id: int, db: Session) -> list:
    """
    Every peer the user has transacted with, showing how THEY rate the
    current user (incoming scores). This matches the leaderboard direction.
    Falls back to 50 if no score exists yet for that pair.
    """
    settled = ["settled", "auto_settled"]

    # Collect all unique peer IDs from transactions
    as_lender   = db.query(Transaction.borrower_id.label("peer_id")).filter(
        Transaction.lender_id == user_id)
    as_borrower = db.query(Transaction.lender_id.label("peer_id")).filter(
        Transaction.borrower_id == user_id)

    peer_ids = union(as_lender, as_borrower).subquery()

    results = (
        db.query(
            User.id,
            User.username,
            func.coalesce(TrustScore.score, 50.0).label("score")
        )
        .select_from(peer_ids)
        .join(User, User.id == peer_ids.c.peer_id)
        .outerjoin(
            TrustScore,
            (TrustScore.user_a_id == User.id) &    # peer is the rater
            (TrustScore.user_b_id == user_id)       # current user is rated
        )
        .distinct()
        .order_by(func.coalesce(TrustScore.score, 50.0).desc())
        .all()
    )

    return [
        {
            "user_id":  r.id,
            "username": r.username,
            "score":    round(float(r.score), 1),
        }
        for r in results
    ]


def leaderboard(db: Session, limit: int = 10) -> list:
    """
    Global trust score = average of all INCOMING scores (how others rate you).
    e.g. if A→you=80 and C→you=60, your global score = 70.
    Users with no incoming scores default to 50.
    """
    from sqlalchemy import func as f, union_all
    from app.models import Transaction

    # Transaction count per user
    as_lender   = db.query(Transaction.lender_id.label("uid"),   func.count().label("cnt")).group_by(Transaction.lender_id)
    as_borrower = db.query(Transaction.borrower_id.label("uid"), func.count().label("cnt")).group_by(Transaction.borrower_id)
    combined    = union_all(as_lender, as_borrower).subquery()
    tx_totals   = (
        db.query(combined.c.uid, func.sum(combined.c.cnt).label("total"))
        .group_by(combined.c.uid)
        .subquery()
    )

    results = (
        db.query(
            User.id,
            User.username,
            func.coalesce(func.avg(TrustScore.score), 50.0).label("avg_score"),
            func.coalesce(tx_totals.c.total, 0).label("tx_count"),
        )
        .outerjoin(TrustScore, TrustScore.user_b_id == User.id)
        .outerjoin(tx_totals,  tx_totals.c.uid == User.id)
        .group_by(User.id, User.username, tx_totals.c.total)
        .order_by(func.coalesce(func.avg(TrustScore.score), 50.0).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "user_id":           r.id,
            "username":          r.username,
            "score":             round(float(r.avg_score), 1),
            "transaction_count": int(r.tx_count),
        }
        for r in results
    ]