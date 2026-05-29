from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=1024)


class UserLogin(BaseModel):
    username: str = Field(..., min_length=1, max_length=320)
    password: str = Field(..., min_length=1, max_length=1024)


class UserRead(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
