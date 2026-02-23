"""Customer service for customer CRUD operations."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.models.customer import new_customer_document
from app.repositories.customer_repository import CustomerRepository
from app.utils.pagination import (
    build_filter_query,
    build_paginated_response,
    build_pagination_query,
)

logger = logging.getLogger(__name__)

CUSTOMER_SEARCH_FIELDS = ["name", "email", "city"]


class CustomerService:
    """Business logic for customer operations."""

    def __init__(self, customer_repo: CustomerRepository):
        self.customer_repo = customer_repo

    async def create_customer(
        self, company_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new customer for the company."""
        doc = new_customer_document(
            company_id=company_id,
            name=data["name"],
            street=data["street"],
            zip_code=data["zip_code"],
            city=data["city"],
            country=data.get("country", "DE"),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            tax_id=data.get("tax_id", ""),
            notes=data.get("notes", ""),
        )
        try:
            customer_id = await self.customer_repo.insert_one(doc)
        except DuplicateKeyError as e:
            if "email" in str(e) or "email_1" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ein Kunde mit dieser E-Mail-Adresse existiert bereits.",
                ) from e
            raise
        logger.info("Created customer %s for company %s", customer_id, company_id)
        return await self.customer_repo.find_by_id(customer_id)

    async def get_customer(self, company_id: str, customer_id: str) -> Dict[str, Any]:
        """Retrieve a single customer, enforcing tenant isolation."""
        customer = await self.customer_repo.find_by_id(customer_id)
        if not customer or customer.get("company_id") != company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )
        return customer

    async def list_customers(
        self,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """List customers with pagination and optional search."""
        extra_filters: Dict[str, Any] = {}
        if is_active is not None:
            extra_filters["is_active"] = is_active

        query = build_filter_query(
            company_id=company_id,
            search=search,
            search_fields=CUSTOMER_SEARCH_FIELDS,
            extra_filters=extra_filters,
        )
        pag = build_pagination_query(page, page_size)
        items = await self.customer_repo.find_many(query, **pag)
        total = await self.customer_repo.count(query)
        return build_paginated_response(items, total, page, page_size)

    async def update_customer(
        self, company_id: str, customer_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update customer fields."""
        await self.get_customer(company_id, customer_id)

        filtered = {k: v for k, v in data.items() if v is not None}
        if not filtered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        updated = await self.customer_repo.update_one(customer_id, filtered)
        logger.info("Updated customer %s", customer_id)
        return updated

    async def delete_customer(self, company_id: str, customer_id: str) -> bool:
        """Soft-delete a customer by deactivating it."""
        await self.get_customer(company_id, customer_id)
        await self.customer_repo.update_one(customer_id, {"is_active": False})
        logger.info("Deactivated customer %s", customer_id)
        return True
