from datetime import datetime
from typing import Sequence

from app.models.comments import Comments
from app.models.posts import Post
from app.repo.feed_repo import FeedRepo
from app.schemas.feed import CommentCreate, PostCreate


class FeedService:
    def __init__(self, repo: FeedRepo) -> None:
        self.repo: FeedRepo = repo

    async def get_posts(
        self, user_id: int, cursor: datetime | None, limit: int
    ) -> Sequence[Post]:
        posts: Sequence[Post] = await self.repo.get_posts_by_categories(
            user_id=user_id, cursor=cursor, limit=limit
        )
        return posts

    async def create_post(self, user_id: int, data: PostCreate) -> Post:
        return await self.repo.create_post(user_id, data)

    async def create_comment(self, data: CommentCreate) -> Comments:
        return await self.repo.create_comment(data)
