from sqlalchemy.orm import Session
from app.models import Wallet


def get_or_create_wallet(user_id: int, db: Session) -> Wallet:
    wallet = db.query(Wallet).filter(Wallet.owner_id == user_id).first()

    if not wallet:
        wallet = Wallet(owner_id=user_id, balance=0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)

    return wallet


def get_balance(user_id: int, db: Session):
    wallet = get_or_create_wallet(user_id, db)
    return wallet.balance


def deposit(user_id: int, amount: float, db: Session):
    wallet = get_or_create_wallet(user_id, db)
    wallet.balance += amount
    db.commit()
    return wallet


def deduct(user_id: int, amount: float, db: Session):
    wallet = get_or_create_wallet(user_id, db)

    if wallet.balance < amount:
        return False  # not enough funds

    wallet.balance -= amount
    db.commit()
    return True