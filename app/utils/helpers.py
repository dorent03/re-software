"""Generic helper utilities."""

from bson import ObjectId
from datetime import datetime
from typing import Any, Dict, Optional


def objectid_to_str(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Convert MongoDB _id (ObjectId) to a string 'id' field."""
    if doc is None:
        return None
    doc["id"] = str(doc.pop("_id"))
    # Convert any nested ObjectId fields
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
    return doc


def now_utc() -> datetime:
    """Return the current UTC datetime."""
    return datetime.utcnow()
