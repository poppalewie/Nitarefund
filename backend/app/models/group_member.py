from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GroupMember(Base):
    __tablename__ = "group_members"

    id: Mapped[int] = mapped_column(primary_key=True)

    group_id: Mapped[int] = mapped_column(ForeignKey("group_transactions.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    share_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)