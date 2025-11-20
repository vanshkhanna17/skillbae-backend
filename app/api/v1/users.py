from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas.user import UserDetails

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/user-details", response_model=UserDetails)
async def get_user(current_user: UserDetails = Depends(get_current_user)):
    return current_user
