from typing import Any, Optional

from fastapi import status

from app.core.exceptions import AppException
from app.repo.user_repo import UserRepo
from app.schemas.user import UserDetails, UserPublic, UserSearchResponse


class UserService:
    def __init__(self, repo: UserRepo) -> None:
        self.repo: UserRepo = repo

    async def get_user(
        self, user_email: Optional[str] = None, user_id: Optional[int] = None
    ) -> UserDetails:
        if user_id:
            user = await self.repo.get_by_id(user_id)
        elif user_email:
            user = await self.repo.get_user_by_email(user_email)
        else:
            user = None
        if not user:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                error="Not Found",
                message="User doesn't exist",
            )
        return UserDetails.model_validate(user)

    async def search_users(
        self, query: str, exclude_user_id: int, limit: int
    ) -> UserSearchResponse:
        users = await self.repo.search_users(query, exclude_user_id, limit)
        return UserSearchResponse(
            items=[UserPublic.model_validate(user) for user in users]
        )

    async def update_user(self, user_id: int, data: dict[str, Any]) -> UserDetails:
        updated = await self.repo.update_user(user_id, data)
        return UserDetails.model_validate(updated)

    async def delete_user(self, user_id: int) -> bool:
        deleted = await self.repo.delete(user_id)
        return deleted

    async def add_categories(self, user_id: int, category_ids: list[int]):
        return await self.repo.add_categories(user_id, category_ids)

    async def add_category(self, user_id: int, category_id: int):
        return await self.repo.add_category(user_id, category_id)

    async def get_categories(self, user_id: int):
        return await self.repo.get_categories(user_id)
