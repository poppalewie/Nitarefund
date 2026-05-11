from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import GroupTransaction, GroupMember, User, Transaction
from app.models.enums import TransactionStatus


def create_group_transaction(current_user, data, db: Session):
    members = db.query(User).filter(User.id.in_(data.user_ids)).all()

    if len(members) != len(data.user_ids):
        raise HTTPException(400, "Some users not found")

    # include creator in split
    total_people = len(members) + 1

    share = float(data.total_amount) / total_people

    group = GroupTransaction(
        creator_id=current_user.id,
        total_amount=data.total_amount,
        description=data.description
    )

    db.add(group)
    db.commit()
    db.refresh(group)

    # create group members + transactions
    for member in members:
        db.add(GroupMember(
            group_id=group.id,
            user_id=member.id,
            share_amount=share
        ))

        tx = Transaction(
            lender_id=current_user.id,
            borrower_id=member.id,
            amount=share,
            description=f"[Group #{group.id}] {data.description}",
            status=TransactionStatus.pending
        )

        db.add(tx)

    db.commit()

    return {"group_id": group.id, "share": share}