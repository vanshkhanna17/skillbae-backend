from app.repo.chats_repo import ChatsRepo


class ChatsService:
    def __init__(self, chats_repo: ChatsRepo) -> None:
        self.chats_repo = chats_repo

    async def create_conversation(self, primary_user_id: int, secondary_user_id: int):
        return await self.chats_repo.create_conversation(
            primary_user_id, secondary_user_id
        )
