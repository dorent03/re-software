"""Product repository for MongoDB product collection operations."""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository):
    """Data access layer for the products collection."""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "products")
