from datetime import datetime
from typing import Optional

from app.schemas.base import BaseSchema
from app.schemas.user import UserDetails


class CommentCreate(BaseSchema):
    comment_text: str
    post_id: int
    user_id: int


class CommentRead(BaseSchema):
    id: int
    publish_date: datetime
    comment_text: str
    user: UserDetails


class Category(BaseSchema):
    id: int
    category: str


class PostCreate(BaseSchema):
    content: str
    category_id: int


class PostRead(PostCreate):
    id: int
    publish_date: datetime
    comments: list[CommentRead]
    category: Category


class PostUpdate(BaseSchema):
    content: Optional[str] = (
        None  # setting equal to None to make field not required in request
    )
    category_id: Optional[int] = None
