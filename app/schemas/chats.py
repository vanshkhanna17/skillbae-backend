from datetime import datetime

from app.schemas.base import BaseSchema
from app.schemas.user import UserDetails


class ConversationCreateRequest(BaseSchema):
    target_user_id: int


class ConversationCreateResponse(BaseSchema):
    conversation_id: str
    created: bool


class MessageCreateRequest(BaseSchema):
    content: str


class Message(BaseSchema):
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


class MessageList(BaseSchema):
    items: list[Message]
    next_cursor: str | None


class MarkReadRequest(BaseSchema):
    last_read_message_id: str


class MarkReadResponse(BaseSchema):
    last_read_message_id: str
    last_read_at: datetime
