from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.services import trust_query_service

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
    return trust_query_service.get_pair_trust(
        current_user.id,
        user_id,
        db
    )


@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    return trust_query_service.leaderboard(db)