from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.auth import UserCreate, Token
from app.services.auth_service import register_user, login_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
def register(data: UserCreate, db: Session = Depends(get_db)):
    result = register_user(data, db)
    return {
        "access_token": result["access_token"],
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    result = login_user(form_data.username, form_data.password, db)
    return {
        "access_token": result["access_token"],
        "token_type": "bearer",
    }