from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas.user import UserDetails

router: APIRouter = APIRouter(prefix="/users")


@router.get(path="/details", response_model=UserDetails)
async def get_user(
    current_user: UserDetails = Depends(get_current_user),
) -> UserDetails:
    return current_user
