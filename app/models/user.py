"""User database model constants and shape definition."""


class UserRole:
    """Available user roles."""

    ADMIN = "ADMIN"
    USER = "USER"

    ALL = [ADMIN, USER]


def new_user_document(
    email: str,
    hashed_password: str,
    first_name: str,
    last_name: str,
    company_id: str,
    role: str = UserRole.USER,
) -> dict:
    """Return a dict representing a new user document for MongoDB insertion."""
    from app.utils.helpers import now_utc

    return {
        "email": email,
        "hashed_password": hashed_password,
        "first_name": first_name,
        "last_name": last_name,
        "company_id": company_id,
        "role": role,
        "is_active": True,
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
