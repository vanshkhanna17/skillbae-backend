from datetime import datetime

from app.schemas.base import BaseSchema
from app.schemas.user import UserDetails


class ConversationCreate(BaseSchema):
    target_user_id: int


class ConversationOut(BaseSchema):
    conversation_id: str
    created: bool


class MessageCreate(BaseSchema):
    content: str


class MessageOut(BaseSchema):
    id: str
    conversation_id: str
    sender_id: int
    content: str
    created_at: datetime
    updated_at: datetime | None
    is_deleted: bool
    message_type: str


class ConversationListItem(BaseSchema):
    conversation_id: str
    other_user: UserDetails
    last_message: str | None
    last_message_at: datetime | None
    unread_count: int


class ConversationList(BaseSchema):
    conversations: list[ConversationListItem]
    next_cursor: str | None
