from typing import Any, Optional

from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_categories import user_categories
from app.schemas.user import UserCreate


class UserRepo:

    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def create_user(self, data: UserCreate, hashed_password: str) -> User:
        new_user = User(
            email=data.email,
            hashed_password=hashed_password,
            first_name=data.first_name,
            last_name=data.last_name,
            avatar_url=data.avatar_url,
            profile=data.profile,
            experience=data.experience,
        )

        try:
            self.session.add(new_user)
            await self.session.commit()
            await self.session.refresh(new_user)
            return new_user
        except IntegrityError:
            await self.session.rollback()
            raise ValueError("Email already exists")

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, user_email: str) -> Optional[User]:
        query = select(User).where(User.email == user_email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def check_email_exists(self, email: str):
        return (await self.get_user_by_email(email)) is not None

    async def update_user(self, user_id: int, data: dict[str, Any]) -> User:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> bool:
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        await self.session.delete(user)
        await self.session.commit()
        return True

    async def add_categories(self, user_id: int, category_ids: list[int]):
        await self.session.execute(
            delete(user_categories).where(user_categories.c.user_id == user_id)
        )

        return await self.session.execute(
            insert(user_categories).values(
                [{"user_id": user_id, "category_id": cid} for cid in category_ids]
            )
        )

    async def add_category(self, user_id: int, category_id: int):
        return await self.session.execute(
            insert(user_categories).values(
                {"user_id": user_id, "category_id": category_id}
            )
        )

    async def get_categories(self, user_id: int):
        categories_result = await self.session.execute(
            select(user_categories.c.category_id).where(
                user_categories.c.user_id == user_id
            )
        )
        return categories_result.scalars().all()
