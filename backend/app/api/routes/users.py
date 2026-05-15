from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
def list_users(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    users = (
        db.query(User)
        .filter(User.id != current_user.id)
        .order_by(User.username)
        .all()
    )
    return [{"id": u.id, "username": u.username} for u in users]