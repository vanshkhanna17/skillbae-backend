from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.user import utc_now

if TYPE_CHECKING:
    from app.models.categories import Categories
    from app.models.comments import Comments


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False, index=True
    )
    publish_date: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, index=True
    )

    comments: Mapped[list["Comments"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    category: Mapped["Categories"] = relationship(back_populates="post")
