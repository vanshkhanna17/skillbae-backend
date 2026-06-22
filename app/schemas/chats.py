from datetime import datetime

from app.schemas.base import BaseSchema


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
    updated_at: datetime
    is_deleted: bool
    message_type: str
