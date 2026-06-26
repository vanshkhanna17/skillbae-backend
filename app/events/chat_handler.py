from app.core.connection_manager import ws_connection_manger
from app.core.event_bus import event_bus
from app.db.session import AsyncSessionLocal
from app.models.chats import ConversationMembers
from app.repo.chats_repo import ChatsRepo


async def get_member_ids(conversation_id: str):
    async with AsyncSessionLocal() as session:
        members: list[ConversationMembers] = await ChatsRepo(
            session
        ).get_conversation_members(conversation_id)
        return [member.user_id for member in members]


async def handle_new_message(channel: str, payload: dict):
    conversation_id = channel.split(":")[1]
    user_ids = await get_member_ids(conversation_id)
    for user_id in user_ids:
        await ws_connection_manger.send_to_user(
            user_id, {"topic": "new_message", "payload": payload}
        )


async def handle_read_receipts(channel: str, payload: dict):
    conversation_id = channel.split(":")[1]
    user_ids = await get_member_ids(conversation_id)
    for user_id in user_ids:
        await ws_connection_manger.send_to_user(
            user_id, {"topic": "read_receipt", "payload": payload}
        )


event_bus.register("conv", "new_messaege", handle_new_message)
event_bus.register("conv", "read_receipt", handle_read_receipts)
