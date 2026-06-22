import json

from app.repo.chats_repo import ChatsRepo
from app.repo.redis_repo import RedisRepo
from app.schemas.chats import MessageCreate


class ChatsService:
    def __init__(self, chats_repo: ChatsRepo, redis_repo: RedisRepo) -> None:
        self.chats_repo: ChatsRepo = chats_repo
        self.redis_repo: RedisRepo = redis_repo

    async def create_conversation(self, primary_user_id: int, secondary_user_id: int):
        return await self.chats_repo.create_conversation(
            primary_user_id, secondary_user_id
        )

    async def is_conversation_member(self, conversation_id: str, user_id: int) -> bool:
        return await self.chats_repo.is_conversation_member(conversation_id, user_id)

    async def send_message(
        self, conversation_id: str, user_id: int, data: MessageCreate
    ):
        message = await self.chats_repo.send_message(conversation_id, user_id, data)
        message_json = json.dumps({
            "type": "new_message",
            "payload": json.loads(message.model_dump_json()),
        })
        await self.redis_repo.publish_content(
            channel=f"conv:{conversation_id}", content=message_json
        )
        return message
