from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

COMMON_PASSWORDS = {
    "password",
    "12345678",
    "qwerty",
    "123456",
    "111111",
    "123456789",
    "iloveyou",
    "admin",
}


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserDetails(BaseSchema):
    id: int
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime
    avatar_url: Optional[str] = None
    profile: Optional[str] = None
    experience: Optional[float] = None
    full_name: Optional[str] = None


class UserCreate(BaseSchema):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=20)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=200)
    profile: Optional[str] = Field(None, max_length=100)
    experience: Optional[float] = Field(None)

    @model_validator(mode="before")
    def check_password_strength(cls, values: dict[str, Any]):
        pwd: str = values.get("password")
        email: str = values.get("email", "") or ""
        low_pwd = pwd.lower()
        errors = []
        if not pwd:
            return values
        if low_pwd in COMMON_PASSWORDS:
            errors.append("Password is too common.")
        if not (re.search(r"[a-z]", pwd) and re.search(r"[A-Z]", pwd)):
            errors.append("Password must contain both uppercase and lowercase letters.")
        if not re.search(r"\d", pwd):
            errors.append("Password must contain at least one digit.")
        if not re.search(r"[^\w\s]", pwd):  # any non-word non-space char
            errors.append(
                "Password must contain at least one special character (e.g. !@#$%)."
            )
        if email and email.lower() in low_pwd:
            errors.append("Password must not contain parts of your email address.")
        if errors:
            raise ValueError(", ".join(errors))
        return values


class UserLogin(BaseSchema):
    email: EmailStr
    password: str


class UserInDb(UserDetails):
    hashed_password: str
