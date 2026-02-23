"""Authentication service handling registration, login, and token refresh."""

import logging
from typing import Any, Dict

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.company import new_company_document
from app.models.user import UserRole, new_user_document
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """Business logic for authentication operations."""

    def __init__(
        self,
        user_repo: UserRepository,
        company_repo: CompanyRepository,
    ):
        self.user_repo = user_repo
        self.company_repo = company_repo

    async def register(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user and create their company tenant."""
        email = data["email"]

        existing = await self.user_repo.find_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

        # Create company first
        company_doc = new_company_document(
            name=data["company_name"],
            street=data["company_street"],
            zip_code=data["company_zip"],
            city=data["company_city"],
            country=data.get("company_country", "DE"),
        )
        try:
            company_id = await self.company_repo.insert_one(company_doc)
        except DuplicateKeyError as exc:
            logger.warning("Duplicate company during registration: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ein Unternehmen mit dieser Steuernummer existiert bereits.",
            ) from exc

        # Create user with ADMIN role (first user in company)
        hashed = hash_password(data["password"])
        user_doc = new_user_document(
            email=email,
            hashed_password=hashed,
            first_name=data["first_name"],
            last_name=data["last_name"],
            company_id=company_id,
            role=UserRole.ADMIN,
        )
        user_id = await self.user_repo.insert_one(user_doc)

        logger.info("Registered user %s for company %s", user_id, company_id)

        tokens = self._generate_tokens(user_id, company_id, UserRole.ADMIN)
        return tokens

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate a user and return JWT tokens."""
        user = await self.user_repo.find_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        if not verify_password(password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        logger.info("User %s logged in", user["id"])
        return self._generate_tokens(user["id"], user["company_id"], user["role"])

    async def refresh(self, refresh_token_str: str) -> Dict[str, Any]:
        """Issue new access and refresh tokens using a valid refresh token."""
        payload = decode_token(refresh_token_str)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user_id = payload.get("sub")
        user = await self.user_repo.find_by_id(user_id)
        if not user or not user.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or deactivated",
            )

        return self._generate_tokens(user["id"], user["company_id"], user["role"])

    @staticmethod
    def _generate_tokens(user_id: str, company_id: str, role: str) -> Dict[str, str]:
        """Create an access + refresh token pair."""
        token_data = {"sub": user_id, "company_id": company_id, "role": role}
        return {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
            "token_type": "bearer",
        }
