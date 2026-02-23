"""Company repository for MongoDB company collection operations."""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository):
    """Data access layer for the companies collection."""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "companies")
