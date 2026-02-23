"""Authentication routes: register, login, refresh, me."""

from fastapi import APIRouter, Depends

from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_auth_service(db=Depends(get_database)) -> AuthService:
    return AuthService(
        user_repo=UserRepository(db),
        company_repo=CompanyRepository(db),
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: RegisterRequest,
    service: AuthService = Depends(_get_auth_service),
):
    """Register a new user and company. Returns JWT tokens."""
    return await service.register(body.dict())


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    service: AuthService = Depends(_get_auth_service),
):
    """Authenticate with email/password. Returns JWT tokens."""
    return await service.login(body.email, body.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    service: AuthService = Depends(_get_auth_service),
):
    """Exchange a valid refresh token for a new token pair."""
    return await service.refresh(body.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return UserResponse(
        id=str(current_user.get("id", current_user.get("_id", ""))),
        email=current_user["email"],
        first_name=current_user["first_name"],
        last_name=current_user["last_name"],
        company_id=str(current_user["company_id"]),
        role=current_user["role"],
        is_active=current_user["is_active"],
    )
