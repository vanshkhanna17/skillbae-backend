from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DECIMAL, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    profile: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    experience: Mapped[Optional[float]] = mapped_column(
        DECIMAL(5, 1),
        nullable=True,
    )

    @property
    def full_name(self) -> str | None:
        if self.first_name or self.last_name:
            return f"{self.first_name or ''} {self.last_name or ''}".strip()
        return None
