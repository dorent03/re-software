"""Product CRUD routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


def _get_product_service(db=Depends(get_database)) -> ProductService:
    return ProductService(product_repo=ProductRepository(db))


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    body: ProductCreate,
    current_user: dict = Depends(get_current_user),
    service: ProductService = Depends(_get_product_service),
):
    """Create a new product."""
    return await service.create_product(
        str(current_user["company_id"]), body.dict()
    )


@router.get("/")
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=100),
    is_active: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_user),
    service: ProductService = Depends(_get_product_service),
):
    """List products with pagination and search."""
    return await service.list_products(
        company_id=str(current_user["company_id"]),
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    current_user: dict = Depends(get_current_user),
    service: ProductService = Depends(_get_product_service),
):
    """Retrieve a single product."""
    return await service.get_product(str(current_user["company_id"]), product_id)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    body: ProductUpdate,
    current_user: dict = Depends(get_current_user),
    service: ProductService = Depends(_get_product_service),
):
    """Update a product's fields."""
    return await service.update_product(
        str(current_user["company_id"]), product_id, body.dict(exclude_unset=True)
    )


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: str,
    current_user: dict = Depends(get_current_user),
    service: ProductService = Depends(_get_product_service),
):
    """Soft-delete (deactivate) a product."""
    await service.delete_product(str(current_user["company_id"]), product_id)
