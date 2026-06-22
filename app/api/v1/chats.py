from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import get_chats_service, get_current_user, get_user_repo
from app.core.exceptions import AppException
from app.repo.user_repo import UserRepo
from app.schemas.chats import (
    ConversationCreate,
    ConversationOut,
    MessageCreate,
    MessageOut,
)
from app.schemas.user import UserDetails
from app.services.chat_service import ChatsService

router: APIRouter = APIRouter(dependencies=[Depends(get_current_user)])

currentUser = Annotated[UserDetails, Depends(get_current_user)]
userRepo = Annotated[UserRepo, Depends(get_user_repo)]
chatService = Annotated[ChatsService, Depends(get_chats_service)]


@router.post("/create")
async def create_new_conversation(
    current_user: currentUser,
    user_repo: userRepo,
    chat_service: chatService,
    data: ConversationCreate,
) -> ConversationOut:
    if data.target_user_id == current_user.id:
        raise AppException(
            status_code=403,
            error="Cannot create chat with self",
            message="Cannot chat with yourself",
        )
    target_user = await user_repo.get_by_id(data.target_user_id)
    if not target_user:
        raise AppException(
            status_code=404, error="User not found", message="User not found"
        )
    return await chat_service.create_conversation(current_user.id, data.target_user_id)


@router.post("/{conversation_id}/message")
async def send_message(
    conversation_id: str,
    current_user: currentUser,
    chat_service: chatService,
    data: MessageCreate,
) -> MessageOut:
    is_member = await chat_service.is_conversation_member(
        conversation_id, current_user.id
    )
    if not is_member:
        raise AppException(
            status_code=403,
            error="Forbidden",
            message="User not part of the conversation",
        )
    return await chat_service.send_message(conversation_id, current_user.id, data)
