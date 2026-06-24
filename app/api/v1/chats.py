from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_chats_service, get_current_user, get_user_repo
from app.core.exceptions import AppException
from app.repo.user_repo import UserRepo
from app.schemas.chats import (
    ConversationCreateRequest,
    ConversationCreateResponse,
    ConversationList,
    MarkReadRequest,
    MarkReadResponse,
    Message,
    MessageCreateRequest,
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
    data: ConversationCreateRequest,
) -> ConversationCreateResponse:
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
    data: MessageCreateRequest,
) -> Message:
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


@router.get("/list")
async def get_conversation_list(
    current_user: currentUser,
    chat_service: chatService,
    cursor: str | None = Query(None, description="Pagination cursor"),
    limit: int = Query(
        20, ge=1, le=100, description="Number of conversations to return"
    ),
) -> ConversationList:
    return await chat_service.get_conversations_list(current_user.id, limit, cursor)


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    current_user: currentUser,
    chat_service: chatService,
    cursor: str | None = Query(None, description="Pagination cursor"),
    limit: int = Query(20, ge=1, le=100, description="Number of messages to return"),
):
    is_member = await chat_service.is_conversation_member(
        conversation_id, current_user.id
    )
    if not is_member:
        raise AppException(
            status_code=403,
            error="Forbidden",
            message="User not part of the conversation",
        )
    return await chat_service.get_conversation_messages(conversation_id, limit, cursor)


@router.post("/{conversation_id}/read")
async def mark_message_read(
    conversation_id: str,
    current_user: currentUser,
    chat_service: chatService,
    data: MarkReadRequest,
) -> MarkReadResponse:
    return await chat_service.mark_messages_read(
        conversation_id, current_user.id, data.last_read_message_id
    )
