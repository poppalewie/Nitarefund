from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models import User
from app.core.security import hash_password, verify_password
from app.schemas.auth import UserCreate, Token, ResetSchema
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

@router.post("/reset-password")
def reset_password(
    data: ResetSchema,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(404, "User not found")

    if not verify_password(data.security_answer, user.security_answer):
        raise HTTPException(403, "Incorrect security answer")
    user.hashed_password = hash_password(data.new_password)
    db.commit()

    return {"message": "Password reset successful"}