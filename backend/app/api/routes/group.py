from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.schemas.group import GroupCreate
from app.services import group_service

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("/")
def create_group(
    data: GroupCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return group_service.create_group_transaction(current_user, data, db)