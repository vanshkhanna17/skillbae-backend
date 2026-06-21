import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import UUID, Boolean, DateTime, Integer, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import ForeignKey

from app.db.base_class import Base
from app.models.user import utc_now


class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"


class Conversations(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint(
            "user_id_low", "user_id_high", name="unique_conversation_pair"
        ),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id_low: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id_high: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ConversationMembers(Base):
    __tablename__ = "conversation_members"

    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    last_read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_read_message_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", use_alter=True, name="fk_last_read_message"),
        nullable=True,
    )


class Messages(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    content: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=utc_now, nullable=True
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    message_type: Mapped[str] = mapped_column(
        SAEnum(MessageType), nullable=False, default=MessageType.TEXT
    )
