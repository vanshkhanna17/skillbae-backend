from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_user_service
from app.core.username import validate_username
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import UserDetails
from app.services.user_service import UserService

router: APIRouter = APIRouter()


@router.get(path="/details", response_model=UserDetails)
async def get_user(
    current_user: UserDetails = Depends(get_current_user),
) -> UserDetails:
    return current_user


@router.put(path="/categories-update")
async def categories_bulk_update(
    data: list[int],
    current_user: UserDetails = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.add_categories(current_user.id, data)


@router.post("/categories-add")
async def add_category(
    category_id: int,
    current_user: UserDetails = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.add_category(current_user.id, category_id)


@router.get("/user-categories")
async def get_categories(
    current_user: UserDetails = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.get_categories(current_user.id)


@router.get(path="/check-username")
async def check_username_availability(
    username: str = Query(..., min_length=3, max_length=30),
    db: AsyncSession = Depends(get_session),
):
    try:
        clean = validate_username(username)
    except ValueError as e:

        return {"available": False, "resaon": str(e)}

    result = await db.execute(select(User).where(User.username == clean))
    exists = result.scalar_one_or_none()

    return {"available": exists is None}
