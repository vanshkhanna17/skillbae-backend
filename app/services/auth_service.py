from fastapi import HTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from app.core.jwt import create_jwt_token
from app.core.security import create_hashed_password, verify_password
from app.repo.user_repo import UserRepo
from app.schemas.user import UserCreate, UserInDb


class AuthService:

    def __init__(self, repo: UserRepo) -> None:
        self.repo: UserRepo = repo

    async def register(self, data: UserCreate):
        existing_user = await self.repo.get_user_by_email(data.email)
        if existing_user:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail="User already exists"
            )
        hashed_password = create_hashed_password(data.password)
        user = await self.repo.create_user(data, hashed_password)
        return UserInDb.model_validate(user)

    async def login(self, email: str, password: str) -> str:
        user = await self.repo.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")

        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
            )
        jwt_token = create_jwt_token(user_id=str(user.id))
        return jwt_token
