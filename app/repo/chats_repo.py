from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.chats import ConversationMembers, Conversations, Messages, MessageType
from app.schemas.chats import ConversationOut, MessageCreate, MessageOut


class ChatsRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_conversation(
        self, primary_user_id: int, secondary_user_id: int
    ) -> ConversationOut:
        user_id_low = min(primary_user_id, secondary_user_id)
        user_id_high = max(primary_user_id, secondary_user_id)

        existing_result = await self.session.execute(
            select(Conversations.id).where(
                Conversations.user_id_low == user_id_low,
                Conversations.user_id_high == user_id_high,
            )
        )
        existing_id = existing_result.scalar_one_or_none()
        if existing_id:
            return ConversationOut(conversation_id=str(existing_id), created=False)

        new_conversation = Conversations(
            user_id_low=user_id_low, user_id_high=user_id_high
        )
        self.session.add(new_conversation)
        await self.session.flush()
        self.session.add_all([
            ConversationMembers(
                conversation_id=new_conversation.id,
                user_id=uid,
            )
            for uid in [primary_user_id, secondary_user_id]
        ])
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            # Race condition: other request created it first, re-query
            result = await self.session.execute(
                select(Conversations.id).where(
                    Conversations.user_id_low == user_id_low,
                    Conversations.user_id_high == user_id_high,
                )
            )
            existing_id = result.scalar_one_or_none()
            if existing_id:
                return ConversationOut(conversation_id=str(existing_id), created=False)
            raise AppException(
                status_code=500,
                error="Something went wrong",
                message="Error creating conversation",
            )
        except Exception as e:
            await self.session.rollback()
            raise AppException(
                status_code=500,
                error="Something went wrong",
                message=f"Error creating conversation: {e}",
            )
        return ConversationOut(conversation_id=str(new_conversation.id), created=True)

    async def is_conversation_member(self, conversation_id: str, user_id: int) -> bool:
        result = await self.session.execute(
            select(ConversationMembers)
            .where(
                ConversationMembers.conversation_id == conversation_id,
                ConversationMembers.user_id == user_id,
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def send_message(
        self, conversation_id: str, user_id: int, data: MessageCreate
    ) -> MessageOut:
        new_message = Messages(
            conversation_id=conversation_id,
            sender_id=user_id,
            content=data.content,
            message_type=MessageType.TEXT,
        )
        self.session.add(new_message)
        await self.session.commit()
        await self.session.refresh(new_message)
        return MessageOut.model_validate(new_message)
