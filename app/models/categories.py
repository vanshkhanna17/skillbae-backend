from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.user_categories import user_categories

if TYPE_CHECKING:
    from app.models.user import User


class Categories(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String, nullable=False)

    users: Mapped[list["User"]] = relationship(
        secondary=user_categories, back_populates="categories"
    )
