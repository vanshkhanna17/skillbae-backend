from datetime import datetime
from typing import Sequence

from fastapi import APIRouter, Depends, Query, Response

from app.core.deps import get_current_user, get_feeds_service
from app.models.comments import Comments
from app.models.posts import Post
from app.schemas.feed import (
    CategoryRead,
    CommentCreate,
    CommentRead,
    PostCreate,
    PostRead,
)
from app.schemas.user import UserDetails
from app.services.feed_service import FeedService

router: APIRouter = APIRouter(dependencies=[Depends(get_current_user)])


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
    return await feed_service.create_comment(current_user.id, data)


@router.get("/categories", response_model=list[CategoryRead])
async def get_all_categories(
    response: Response,
    feed_service: FeedService = Depends(get_feeds_service),
):
    response.headers["Cache-Control"] = "public, max-age=900"
    return await feed_service.get_categories()


@router.get("/post-comments/{post_id}", response_model=list[CommentRead])
async def get_post_comments(
    post_id: int,
    feed_service: FeedService = Depends(get_feeds_service),
    cursor: datetime | None = Query(None, description="Pagination cursor"),
    limit: int = Query(20, ge=1, le=100, description="Number of comments to return"),
) -> Sequence[Comments]:
    return await feed_service.get_post_comments(post_id, cursor, limit)
