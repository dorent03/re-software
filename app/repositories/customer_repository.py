"""Customer repository for MongoDB customer collection operations."""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository):
    """Data access layer for the customers collection."""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "customers")
