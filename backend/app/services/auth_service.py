from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import User
from app.core.security import hash_password, verify_password, create_access_token


def register_user(data, db: Session):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(400, "Email already registered")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        security_answer=hash_password(data.security_answer.lower().strip())
        if data.security_answer
        else None,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.username})

    return {"access_token": token, "user": user}


def login_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(401, "Invalid username or password")

    token = create_access_token({"sub": user.username})

    return {"access_token": token, "user": user}