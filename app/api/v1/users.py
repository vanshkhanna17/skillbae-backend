from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_user_service
from app.schemas.user import UserDetails
from app.services.user_service import UserService

router: APIRouter = APIRouter(prefix="/users")


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
    return user_service.add_categories(current_user.id, data)


@router.post("/categories-add")
async def add_category(
    category_id: int,
    current_user: UserDetails = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.add_category(current_user.id, category_id)


@router.get("/user-categories")
async def get_categories(
    current_user: UserDetails = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.get_categories(current_user.id)
