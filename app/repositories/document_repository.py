"""Document repository for MongoDB document collection operations."""

from typing import Any, Dict, List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.repositories.base import BaseRepository
from app.utils.helpers import objectid_to_str, now_utc


class DocumentRepository(BaseRepository):
    """Data access layer for the documents collection."""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "documents")

    async def find_by_number(
        self, company_id: str, document_number: str
    ) -> Optional[Dict[str, Any]]:
        """Find a document by its unique number within a company."""
        doc = await self.collection.find_one(
            {"company_id": company_id, "document_number": document_number}
        )
        return objectid_to_str(doc)

    async def add_payment(
        self, document_id: str, payment: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Push a payment record and update totals atomically."""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(document_id)},
            {
                "$push": {"payments": payment},
                "$inc": {
                    "totals.paid_amount": payment["amount"],
                    "totals.remaining_amount": -payment["amount"],
                },
                "$set": {"updated_at": now_utc()},
            },
            return_document=ReturnDocument.AFTER,
        )
        return objectid_to_str(result)

    async def add_reminder(
        self, document_id: str, reminder: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Push a reminder record onto the document."""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(document_id)},
            {
                "$push": {"reminders": reminder},
                "$set": {"updated_at": now_utc()},
            },
            return_document=ReturnDocument.AFTER,
        )
        return objectid_to_str(result)

    async def find_related_documents(
        self, company_id: str, related_document_id: str
    ) -> List[Dict[str, Any]]:
        """Find all documents linked to a given document."""
        cursor = self.collection.find({
            "company_id": company_id,
            "related_document_id": related_document_id,
        }).sort("created_at", -1)
        docs = await cursor.to_list(length=100)
        return [objectid_to_str(doc) for doc in docs]

    async def aggregate_monthly_revenue(
        self, company_id: str
    ) -> List[Dict[str, Any]]:
        """Aggregate paid invoice totals grouped by year+month."""
        pipeline = [
            {
                "$match": {
                    "company_id": company_id,
                    "document_type": "INVOICE",
                    "status": "PAID",
                }
            },
            {
                "$addFields": {
                    "issue_date_parsed": {
                        "$dateFromString": {
                            "dateString": "$issue_date",
                            "format": "%Y-%m-%d",
                            "onError": None,
                        }
                    }
                }
            },
            {"$match": {"issue_date_parsed": {"$ne": None}}},
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$issue_date_parsed"},
                        "month": {"$month": "$issue_date_parsed"},
                    },
                    "total_gross": {"$sum": "$totals.gross"},
                    "total_net": {"$sum": "$totals.net"},
                    "total_vat": {"$sum": "$totals.vat"},
                    "invoice_count": {"$sum": 1},
                }
            },
            {"$sort": {"_id.year": 1, "_id.month": 1}},
            {
                "$project": {
                    "_id": 0,
                    "year": "$_id.year",
                    "month": "$_id.month",
                    "total_gross": {"$round": ["$total_gross", 2]},
                    "total_net": {"$round": ["$total_net", 2]},
                    "total_vat": {"$round": ["$total_vat", 2]},
                    "invoice_count": 1,
                }
            },
        ]
        return await self.collection.aggregate(pipeline).to_list(length=500)

    async def aggregate_revenue_by_customer(
        self, company_id: str
    ) -> List[Dict[str, Any]]:
        """Aggregate paid invoice totals grouped by customer."""
        pipeline = [
            {
                "$match": {
                    "company_id": company_id,
                    "document_type": "INVOICE",
                    "status": "PAID",
                }
            },
            {
                "$group": {
                    "_id": "$customer_id",
                    "total_gross": {"$sum": "$totals.gross"},
                    "total_net": {"$sum": "$totals.net"},
                    "invoice_count": {"$sum": 1},
                }
            },
            {"$sort": {"total_gross": -1}},
            {
                "$project": {
                    "_id": 0,
                    "customer_id": "$_id",
                    "total_gross": {"$round": ["$total_gross", 2]},
                    "total_net": {"$round": ["$total_net", 2]},
                    "invoice_count": 1,
                }
            },
        ]
        return await self.collection.aggregate(pipeline).to_list(length=500)


class CounterRepository:
    """Handles atomic counter increments for sequential document numbering."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["counters"]

    async def get_next_number(self, company_id: str, counter_type: str) -> int:
        """Atomically increment and return the next sequential number."""
        result = await self.collection.find_one_and_update(
            {"company_id": company_id, "counter_type": counter_type},
            {"$inc": {"sequence": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return result["sequence"]
