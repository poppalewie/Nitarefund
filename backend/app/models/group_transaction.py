from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GroupTransaction(Base):
    __tablename__ = "group_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )