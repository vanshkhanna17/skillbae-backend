import base64
import json
from datetime import datetime

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.exceptions import AppException
from app.models.chats import ConversationMembers, Conversations, Messages, MessageType
from app.models.user import User
from app.schemas.chats import (
    ConversationList,
    ConversationListItem,
    ConversationOut,
    MessageCreate,
    MessageOut,
)
from app.schemas.user import UserDetails


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
        return MessageOut(
            id=str(new_message.id),
            conversation_id=str(new_message.conversation_id),
            sender_id=new_message.sender_id,
            content=new_message.content,
            created_at=new_message.created_at,
            updated_at=new_message.updated_at,
            is_deleted=new_message.is_deleted,
            message_type=new_message.message_type.value,
        )

    async def get_conversations_list(
        self, user_id: int, limit: int, cursor: str | None = None
    ) -> ConversationList:
        msg_ranked = (
            select(
                Messages.conversation_id,
                Messages.content.label("last_message"),
                Messages.created_at.label("last_message_at"),
                func
                .row_number()
                .over(
                    partition_by=Messages.conversation_id,
                    order_by=Messages.created_at.desc(),
                )
                .label("rn"),
            )
            .where(Messages.is_deleted.is_(False))
            .subquery("msg_ranked")
        )

        latest_msg = (
            select(
                msg_ranked.c.conversation_id,
                msg_ranked.c.last_message,
                msg_ranked.c.last_message_at,
            )
            .where(msg_ranked.c.rn == 1)
            .subquery("latest_msg")
        )

        unread_count = (
            select(
                Messages.conversation_id, func.count(Messages.id).label("unread_count")
            )
            .join(
                target=ConversationMembers,
                onclause=and_(
                    ConversationMembers.conversation_id == Messages.conversation_id,
                    ConversationMembers.user_id == user_id,
                ),
            )
            .where(
                Messages.is_deleted.is_(False),
                Messages.sender_id != user_id,
                case(
                    (ConversationMembers.last_read_at.is_(None), True),
                    else_=(Messages.created_at > ConversationMembers.last_read_at),
                ),
            )
            .group_by(Messages.conversation_id)
            .subquery("unread_count")
        )

        OtherMember = aliased(ConversationMembers)

        query = (
            select(
                ConversationMembers.conversation_id,
                User,
                latest_msg.c.last_message,
                latest_msg.c.last_message_at,
                unread_count.c.unread_count,
            )
            .where(ConversationMembers.user_id == user_id)
            .join(
                target=OtherMember,
                onclause=and_(
                    OtherMember.conversation_id == ConversationMembers.conversation_id,
                    OtherMember.user_id != user_id,
                ),
            )
            .join(User, onclause=User.id == OtherMember.user_id)
            .outerjoin(
                target=latest_msg,
                onclause=latest_msg.c.conversation_id
                == ConversationMembers.conversation_id,
            )
            .outerjoin(
                target=unread_count,
                onclause=unread_count.c.conversation_id
                == ConversationMembers.conversation_id,
            )
        )

        if cursor:
            decoded_cursor = json.loads(base64.b64decode(cursor))
            cursor_ts_raw = decoded_cursor["last_message_at"]
            cursor_cid = decoded_cursor["conversation_id"]

            if cursor_ts_raw is not None:
                cursor_ts = datetime.fromisoformat(cursor_ts_raw)
                query = query.where(
                    or_(
                        latest_msg.c.last_message_at < cursor_ts,
                        and_(
                            latest_msg.c.last_message_at == cursor_ts,
                            ConversationMembers.conversation_id > cursor_cid,
                        ),
                        latest_msg.c.last_message_at.is_(None),
                    )
                )
            else:
                query = query.where(
                    latest_msg.c.last_message_at.is_(None),
                    ConversationMembers.conversation_id > cursor_cid,
                )

        query = query.order_by(
            latest_msg.c.last_message_at.desc().nulls_last(),
            ConversationMembers.conversation_id.asc(),
        ).limit(limit + 1)

        result = await self.session.execute(query)
        rows = result.all()
        has_next = len(rows) > limit
        items = rows[:limit]
        next_cursor = None
        if has_next:
            last = items[-1]
            next_cursor = base64.b64encode(
                json.dumps({
                    "last_message_at": (
                        last.last_message_at.isoformat()
                        if last.last_message_at
                        else None
                    ),
                    "conversation_id": str(last.conversation_id),
                }).encode()
            ).decode()
        conversations: list[ConversationListItem] = [
            ConversationListItem(
                conversation_id=str(item.conversation_id),
                other_user=UserDetails.model_validate(item.User),
                last_message=item.last_message,
                last_message_at=item.last_message_at,
                unread_count=item.unread_count or 0,
            )
            for item in items
        ]
        return ConversationList(conversations=conversations, next_cursor=next_cursor)
