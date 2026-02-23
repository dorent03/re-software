"""Base repository with shared CRUD operations for MongoDB collections."""

from typing import Any, Dict, List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.helpers import objectid_to_str, now_utc


class BaseRepository:
    """Generic async MongoDB repository providing CRUD primitives."""

    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str):
        self.db = db
        self.collection = db[collection_name]

    async def find_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single document by its _id."""
        doc = await self.collection.find_one({"_id": ObjectId(document_id)})
        return objectid_to_str(doc)

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve a single document matching the query."""
        doc = await self.collection.find_one(query)
        return objectid_to_str(doc)

    async def find_many(
        self,
        query: Dict[str, Any],
        skip: int = 0,
        limit: int = 20,
        sort: Optional[List] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve multiple documents with pagination."""
        cursor = self.collection.find(query).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        else:
            cursor = cursor.sort("created_at", -1)
        docs = await cursor.to_list(length=limit)
        return [objectid_to_str(doc) for doc in docs]

    async def count(self, query: Dict[str, Any]) -> int:
        """Count documents matching the query."""
        return await self.collection.count_documents(query)

    async def insert_one(self, document: Dict[str, Any]) -> str:
        """Insert a single document and return its string ID."""
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def update_one(
        self, document_id: str, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a document by ID. Returns the updated document or None."""
        update_data["updated_at"] = now_utc()
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(document_id)},
            {"$set": update_data},
            return_document=True,
        )
        return objectid_to_str(result)

    async def delete_one(self, document_id: str) -> bool:
        """Delete a document by ID. Returns True if deleted."""
        result = await self.collection.delete_one({"_id": ObjectId(document_id)})
        return result.deleted_count > 0
