from datetime import datetime
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comments import Comments
from app.models.posts import Post
from app.models.user_categories import user_categories
from app.schemas.feed import CommentCreate, PostCreate, PostUpdate


class FeedRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_posts_by_categories(
        self, user_id: int, cursor: datetime | None, limit: int
    ) -> Sequence[Post]:
        posts_query = (
            select(Post)
            .join(user_categories, Post.category_id == user_categories.c.category_id)
            .where(user_categories.c.user_id == user_id)
        )

        if cursor:
            posts_query = posts_query.where(Post.publish_date < cursor)

        posts_query = posts_query.order_by(Post.publish_date.desc()).limit(limit)
        posts_result = await self.session.execute(posts_query)
        return posts_result.scalars().all()

    async def get_user_posts(self, user_id: int) -> Sequence[Post]:
        posts_query = select(Post).where(Post.user_id == user_id)
        posts_result = await self.session.execute(posts_query)
        return posts_result.scalars().all()

    async def create_post(self, user_id: int, post_data: PostCreate) -> Post:
        new_post = Post(
            content=post_data.content,
            category_id=post_data.category_id,
            user_id=user_id,
        )
        try:
            self.session.add(new_post)
            await self.session.commit()
            await self.session.refresh(new_post)
            return new_post
        except DatabaseError as e:
            await self.session.rollback()
            raise e

    async def update_post(self, post_id: int, post_data: PostUpdate):
        query = (
            update(Post)
            .where(Post.id == post_id)
            .values(**post_data.model_dump(exclude_unset=True))
            .returning(Post)
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def create_comment(self, data: CommentCreate) -> Comments:
        new_comment = Comments(**data.model_dump())
        try:
            self.session.add(new_comment)
            await self.session.commit()
            await self.session.refresh(new_comment)
            return new_comment
        except DatabaseError as e:
            await self.session.rollback()
            raise e
