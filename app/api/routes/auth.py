from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import load_settings
from app.deps import get_auth_service
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserRead
from app.security import check_login_rate_limit, create_access_token, require_current_user
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(body: UserCreate, auth: AuthService = Depends(get_auth_service)) -> UserRead:
    if not load_settings().allow_signup:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Signup is disabled")
    try:
        return auth.register(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/login", response_model=TokenResponse)
def login(
    body: UserLogin,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    check_login_rate_limit(request, body.username)
    user = auth.authenticate(body.username, body.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return TokenResponse(access_token=create_access_token(user))


@router.get("/me", response_model=UserRead)
def me(user: UserRead = Depends(require_current_user)) -> UserRead:
    return user
