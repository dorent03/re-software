"""Product service for product CRUD operations."""

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, status

from app.models.product import new_product_document
from app.repositories.product_repository import ProductRepository
from app.utils.pagination import (
    build_filter_query,
    build_paginated_response,
    build_pagination_query,
)

logger = logging.getLogger(__name__)

PRODUCT_SEARCH_FIELDS = ["name", "description"]


class ProductService:
    """Business logic for product operations."""

    def __init__(self, product_repo: ProductRepository):
        self.product_repo = product_repo

    async def create_product(
        self, company_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new product."""
        doc = new_product_document(
            company_id=company_id,
            name=data["name"],
            description=data.get("description", ""),
            unit=data.get("unit", "Stück"),
            unit_price=data["unit_price"],
            vat_rate=data.get("vat_rate", 0.19),
        )
        product_id = await self.product_repo.insert_one(doc)
        logger.info("Created product %s for company %s", product_id, company_id)
        return await self.product_repo.find_by_id(product_id)

    async def get_product(self, company_id: str, product_id: str) -> Dict[str, Any]:
        """Retrieve a single product, enforcing tenant isolation."""
        product = await self.product_repo.find_by_id(product_id)
        if not product or product.get("company_id") != company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return product

    async def list_products(
        self,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """List products with pagination and optional search."""
        extra_filters: Dict[str, Any] = {}
        if is_active is not None:
            extra_filters["is_active"] = is_active

        query = build_filter_query(
            company_id=company_id,
            search=search,
            search_fields=PRODUCT_SEARCH_FIELDS,
            extra_filters=extra_filters,
        )
        pag = build_pagination_query(page, page_size)
        items = await self.product_repo.find_many(query, **pag)
        total = await self.product_repo.count(query)
        return build_paginated_response(items, total, page, page_size)

    async def update_product(
        self, company_id: str, product_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update product fields."""
        await self.get_product(company_id, product_id)

        filtered = {k: v for k, v in data.items() if v is not None}
        if not filtered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        updated = await self.product_repo.update_one(product_id, filtered)
        logger.info("Updated product %s", product_id)
        return updated

    async def delete_product(self, company_id: str, product_id: str) -> bool:
        """Soft-delete a product by deactivating it."""
        await self.get_product(company_id, product_id)
        await self.product_repo.update_one(product_id, {"is_active": False})
        logger.info("Deactivated product %s", product_id)
        return True
