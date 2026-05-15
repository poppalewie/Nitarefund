from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.services.wallet_service import get_balance

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/balance")
def balance(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return {"balance": float(get_balance(current_user.id, db))}