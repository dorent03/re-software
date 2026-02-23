"""Shared pagination utilities."""

from typing import Any, Dict, List, Optional


def build_pagination_query(
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, int]:
    """Calculate skip and limit values for MongoDB queries."""
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    return {
        "skip": (page - 1) * page_size,
        "limit": page_size,
    }


def build_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
) -> Dict[str, Any]:
    """Wrap a list of items with pagination metadata."""
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    total_pages = max((total + page_size - 1) // page_size, 1)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def build_filter_query(
    company_id: str,
    search: Optional[str] = None,
    search_fields: Optional[List[str]] = None,
    extra_filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a MongoDB filter dict scoped to a company with optional text search."""
    query: Dict[str, Any] = {"company_id": company_id}

    if search and search_fields:
        or_conditions = [
            {field: {"$regex": search, "$options": "i"}}
            for field in search_fields
        ]
        query["$or"] = or_conditions

    if extra_filters:
        query.update(extra_filters)

    return query
