from datetime import datetime
from typing import Sequence

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_feeds_service
from app.models.comments import Comments
from app.models.posts import Post
from app.schemas.feed import CommentCreate, CommentRead, PostCreate, PostRead
from app.schemas.user import UserDetails
from app.services.feed_service import FeedService

router: APIRouter = APIRouter()


@router.get("/posts", response_model=list[PostRead])
async def get_posts(
    current_user: UserDetails = Depends(get_current_user),
    feed_service: FeedService = Depends(get_feeds_service),
    cursor: datetime | None = Query(None, description="Pagination cursor"),
    limit: int = Query(20, ge=1, le=100, description="Number of posts to return"),
) -> Sequence[Post]:
    return await feed_service.get_posts(current_user.id, cursor, limit)


@router.post("/posts", response_model=PostRead)
async def create_post(
    data: PostCreate,
    current_user: UserDetails = Depends(get_current_user),
    feed_service: FeedService = Depends(get_feeds_service),
) -> Post:
    return await feed_service.create_post(current_user.id, data)


@router.post("/comment", response_model=CommentRead)
async def create_comment(
    data: CommentCreate,
    current_user: UserDetails = Depends(get_current_user),
    feed_service: FeedService = Depends(get_feeds_service),
) -> Comments:
    data.user_id = current_user.id
    return await feed_service.create_comment(data)


@router.get("/categories")
async def get_all_categories(
    current_user: UserDetails = Depends(get_current_user),
    feed_service: FeedService = Depends(get_feeds_service),
):
    return await feed_service.get_categories()
