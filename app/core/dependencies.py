"""Shared FastAPI dependencies for authentication and authorization."""

from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.database import get_database
from app.core.security import decode_token
from app.models.user import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Decode the JWT access token and return the authenticated user document."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    token_type = payload.get("type")
    if token_type != "access":
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    db = get_database()
    from bson import ObjectId
    from app.utils.helpers import objectid_to_str

    user = await db.users.find_one({"_id": ObjectId(user_id), "is_active": True})
    if user is None:
        raise credentials_exception

    return objectid_to_str(user)


def require_roles(allowed_roles: List[str]):
    """Return a dependency that restricts access to users with specified roles."""

    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


def require_admin(current_user: dict = Depends(require_roles([UserRole.ADMIN]))):
    """Shortcut dependency that requires ADMIN role."""
    return current_user
