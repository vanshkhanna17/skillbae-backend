from typing import Any, Optional

from fastapi import HTTPException, status

from app.repo.user_repo import UserRepo
from app.schemas.user import UserDetails


class UserService:

    def __init__(self, repo: UserRepo) -> None:
        self.repo: UserRepo = repo

    async def get_user(
        self, user_email: str, user_id: Optional[int] = None
    ) -> UserDetails:
        if user_id:
            user = self.repo.get_user_by_id(user_id)
        else:
            user = await self.repo.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return UserDetails.model_validate(user)

    async def update_user(self, user_id: int, data: dict[str, Any]) -> UserDetails:
        updated = await self.repo.update_user(user_id, data)
        return UserDetails.model_validate(updated)

    async def delete_user(self, user_id: int) -> bool:
        deleted = await self.repo.delete_user(user_id)
        return deleted
