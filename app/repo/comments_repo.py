from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import selectinload

from app.models.comments import Comments
from app.repo.base_repo import BaseRepo
from app.schemas.feed import CommentCreate


class CommentsRepo(BaseRepo):

    async def create(self, data: CommentCreate, **kwargs: object) -> Comments:
        new_comment = Comments(user_id=kwargs["user_id"], **data.model_dump())
        try:
            self.session.add(new_comment)
            await self.session.commit()
            await self.session.refresh(new_comment)
            return new_comment
        except DatabaseError as e:
            await self.session.rollback()
            raise e

    async def get_by_id(self, id: int) -> Comments | None:
        comment_query = select(Comments).where(Comments.id == id)
        comment = await self.session.execute(comment_query)
        return comment.scalar_one_or_none()

    async def delete(self, id: int) -> bool:
        comment = await self.get_by_id(id)
        if not comment:
            return False
        await self.session.delete(comment)
        await self.session.commit()
        return True

    async def get_post_comments(
        self, post_id: int, cursor: datetime | None, limit: int
    ) -> Sequence[Comments]:
        comments_query = (
            select(Comments)
            .where(Comments.post_id == post_id)
            .options(selectinload(Comments.user))
        )
        if cursor:
            comments_query = comments_query.where(Comments.publish_date < cursor)
        comments_query = comments_query.order_by(Comments.publish_date.desc()).limit(
            limit
        )
        result = await self.session.execute(comments_query)
        return result.scalars().all()
