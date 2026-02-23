"""User repository for MongoDB user collection operations."""

from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.base import BaseRepository
from app.utils.helpers import objectid_to_str


class UserRepository(BaseRepository):
    """Data access layer for the users collection."""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "users")

    async def find_by_email_and_company(
        self, email: str, company_id: str
    ) -> Optional[Dict[str, Any]]:
        """Look up a user by email within a specific company."""
        doc = await self.collection.find_one(
            {"email": email, "company_id": company_id}
        )
        return objectid_to_str(doc)

    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Look up a user by email (across all companies)."""
        doc = await self.collection.find_one({"email": email})
        return objectid_to_str(doc)
