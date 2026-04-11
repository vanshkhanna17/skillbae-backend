from datetime import datetime
from typing import Sequence

from app.models.categories import Categories
from app.models.comments import Comments
from app.models.posts import Post
from app.repo.comments_repo import CommentsRepo
from app.repo.feed_repo import FeedRepo
from app.schemas.feed import CommentCreate, PostCreate


class FeedService:
    def __init__(self, feed_repo: FeedRepo, comments_repo: CommentsRepo) -> None:
        self.feed_repo: FeedRepo = feed_repo
        self.comments_repo: CommentsRepo = comments_repo

    async def get_posts(
        self, user_id: int, cursor: datetime | None, limit: int
    ) -> Sequence[Post]:
        posts: Sequence[Post] = await self.feed_repo.get_posts_by_categories(
            user_id=user_id, cursor=cursor, limit=limit
        )
        return posts

    async def create_post(self, user_id: int, data: PostCreate) -> Post:
        return await self.feed_repo.create_post(user_id, data)

    async def create_comment(self, user_id: int, data: CommentCreate) -> Comments:
        return await self.comments_repo.create(data, user_id=user_id)

    async def get_categories(self) -> Sequence[Categories]:
        return await self.feed_repo.get_categories()

    async def get_post_comments(
        self, post_id: int, cursor: datetime | None, limit: int
    ) -> Sequence[Comments]:
        return await self.comments_repo.get_post_comments(post_id, cursor, limit)
