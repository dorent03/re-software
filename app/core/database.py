"""Async MongoDB connection management using Motor."""

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDBManager:
    """Manages the async MongoDB connection lifecycle."""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """Establish connection to MongoDB."""
        logger.info("Connecting to MongoDB at %s", settings.MONGODB_URL)
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB_NAME]
        await self.client.admin.command("ping")
        logger.info("Connected to MongoDB database: %s", settings.MONGODB_DB_NAME)

    async def disconnect(self) -> None:
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    def get_database(self) -> AsyncIOMotorDatabase:
        """Return the active database instance."""
        if self.db is None:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return self.db

    async def create_indexes(self) -> None:
        """Create required indexes for all collections."""
        db = self.get_database()

        # Users: unique email per company
        await db.users.create_index(
            [("email", 1), ("company_id", 1)],
            unique=True,
        )

        # Companies: unique tax_id (only when tax_id is a non-empty string)
        try:
            await db.companies.drop_index("tax_id_1")
        except Exception:
            pass
        await db.companies.create_index(
            "tax_id",
            unique=True,
            partialFilterExpression={"tax_id": {"$type": "string", "$gt": ""}},
        )

        # Customers: index by company
        await db.customers.create_index("company_id")
        try:
            await db.customers.drop_index("email_1_company_id_1")
        except Exception:
            pass
        await db.customers.create_index(
            [("email", 1), ("company_id", 1)],
            unique=True,
            partialFilterExpression={"email": {"$type": "string", "$gt": ""}},
        )

        # Products: index by company
        await db.products.create_index("company_id")

        # Documents: compound indexes for efficient queries
        await db.documents.create_index("company_id")
        await db.documents.create_index(
            [("company_id", 1), ("document_type", 1), ("status", 1)]
        )
        await db.documents.create_index(
            [("company_id", 1), ("document_number", 1)],
            unique=True,
        )
        await db.documents.create_index(
            [("company_id", 1), ("related_document_id", 1)]
        )
        await db.documents.create_index(
            [("company_id", 1), ("status", 1), ("due_date", 1)]
        )

        # Counters: unique key per company + type
        await db.counters.create_index(
            [("company_id", 1), ("counter_type", 1)],
            unique=True,
        )

        logger.info("Database indexes created successfully")


mongodb = MongoDBManager()


def get_database() -> AsyncIOMotorDatabase:
    """Dependency-injection helper that returns the database instance."""
    return mongodb.get_database()
