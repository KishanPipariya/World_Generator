from __future__ import annotations

from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from time import monotonic
from typing import Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import load_settings
from app.deps import get_auth_service, get_world_service
from app.schemas.auth import UserRead
from app.services.auth_service import AuthService
from app.services.world_service import WorldService, reset_current_owner_id, set_current_owner_id

_bearer = HTTPBearer(auto_error=False)
_login_attempts: dict[str, deque[float]] = defaultdict(deque)
_generation_attempts: dict[str, deque[float]] = defaultdict(deque)


def create_access_token(user: UserRead) -> str:
    settings = load_settings()
    expires = datetime.now(UTC) + timedelta(minutes=settings.jwt_expires_minutes)
    payload: dict[str, Any] = {"sub": str(user.id), "username": user.username, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def _decode_token(token: str) -> UUID:
    settings = load_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        subject = payload.get("sub")
        if not subject:
            raise jwt.InvalidTokenError
        return UUID(str(subject))
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    auth: AuthService = Depends(get_auth_service),
) -> UserRead:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = auth.get_user_by_id(_decode_token(credentials.credentials))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_current_user(user: UserRead = Depends(get_current_user)):
    token = set_current_owner_id(str(user.id))
    try:
        yield user
    finally:
        reset_current_owner_id(token)


def require_world_access(
    request: Request,
    _user: UserRead = Depends(require_current_user),
    svc: WorldService = Depends(get_world_service),
) -> None:
    raw_world_id = request.path_params.get("world_id")
    if raw_world_id is None:
        return
    try:
        world_id = UUID(str(raw_world_id))
    except ValueError:
        return
    if svc.get(world_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")


def _check_window(bucket: dict[str, deque[float]], key: str, *, limit: int, seconds: int) -> None:
    now = monotonic()
    attempts = bucket[key]
    while attempts and now - attempts[0] > seconds:
        attempts.popleft()
    if len(attempts) >= limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    attempts.append(now)


def check_login_rate_limit(request: Request, username: str) -> None:
    client = request.client.host if request.client else "unknown"
    _check_window(_login_attempts, f"{client}:{username.lower()}", limit=8, seconds=300)


def check_generation_rate_limit(user: UserRead = Depends(get_current_user)) -> UserRead:
    _check_window(_generation_attempts, str(user.id), limit=20, seconds=300)
    return user
