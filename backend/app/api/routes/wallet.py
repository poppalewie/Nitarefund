from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.services.wallet_service import get_balance
from app.models import Wallet, User, Transaction
from app.models.enums import TransactionStatus

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/balance")
def balance(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return {"balance": float(get_balance(current_user.id, db))}


@router.get("/leaderboard")
def wallet_leaderboard(db: Session = Depends(get_db)):
    """Public — top 10 wallets by balance."""
    results = (
        db.query(Wallet.balance, User.username)
        .join(User, User.id == Wallet.owner_id)
        .filter(Wallet.balance > 0)
        .order_by(Wallet.balance.desc())
        .limit(10)
        .all()
    )
    return [
        {"username": r.username, "balance": float(r.balance)}
        for r in results
    ]


@router.get("/categories")
def spending_categories(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Breakdown of how much the user has been involved in per category,
    derived from transaction descriptions using keyword matching.
    """
    settled = [TransactionStatus.settled, TransactionStatus.auto_settled]
    uid = current_user.id

    txns = db.query(Transaction).filter(
        or_(Transaction.lender_id == uid, Transaction.borrower_id == uid),
        Transaction.status.in_(settled)
    ).all()

    CATEGORY_KEYWORDS = {
        "Food & Drink":  ["food", "lunch", "dinner", "breakfast", "drinks",
                          "coffee", "tea", "snack", "meal", "java", "kfc",
                          "restaurant", "eat", "bar", "beers", "fare"],
        "Transport":     ["uber", "taxi", "fare", "matatu", "bus", "bolt",
                          "ride", "petrol", "fuel", "transport"],
        "Rent & Bills":  ["rent", "bill", "electricity", "water", "wifi",
                          "internet", "utilities", "house"],
        "Shopping":      ["shopping", "market", "groceries", "supermarket",
                          "mall", "clothes", "shoes"],
        "Entertainment": ["movie", "cinema", "concert", "event", "ticket",
                          "game", "party", "club", "netflix"],
        "Services":      ["service", "repair", "fix", "work", "job",
                          "project", "design", "code"],
        "Education":     ["school", "fee", "tuition", "book", "course",
                          "study", "class", "exam"],
    }

    categories = {k: 0.0 for k in CATEGORY_KEYWORDS}
    categories["Other"] = 0.0

    for tx in txns:
        desc = (tx.description or "").lower()
        matched = False
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in desc for kw in keywords):
                categories[cat] += float(tx.amount)
                matched = True
                break
        if not matched:
            categories["Other"] += float(tx.amount)

    return [
        {"category": k, "amount": round(v, 2)}
        for k, v in sorted(categories.items(), key=lambda x: x[1], reverse=True)
        if v > 0
    ]