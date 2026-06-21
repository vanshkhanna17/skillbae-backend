from app.schemas.base import BaseSchema


class ConversationCreate(BaseSchema):
    target_user_id: int


class ConversationOut(BaseSchema):
    conversation_id: str
    created: bool
