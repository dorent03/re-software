"""Customer CRUD routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


def _get_customer_service(db=Depends(get_database)) -> CustomerService:
    return CustomerService(customer_repo=CustomerRepository(db))


@router.post("/", response_model=CustomerResponse, status_code=201)
async def create_customer(
    body: CustomerCreate,
    current_user: dict = Depends(get_current_user),
    service: CustomerService = Depends(_get_customer_service),
):
    """Create a new customer for the user's company."""
    return await service.create_customer(
        str(current_user["company_id"]), body.dict()
    )


@router.get("/")
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=100),
    is_active: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_user),
    service: CustomerService = Depends(_get_customer_service),
):
    """List customers with pagination and search."""
    return await service.list_customers(
        company_id=str(current_user["company_id"]),
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    service: CustomerService = Depends(_get_customer_service),
):
    """Retrieve a single customer by ID."""
    return await service.get_customer(
        str(current_user["company_id"]), customer_id
    )


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    body: CustomerUpdate,
    current_user: dict = Depends(get_current_user),
    service: CustomerService = Depends(_get_customer_service),
):
    """Update a customer's fields."""
    return await service.update_customer(
        str(current_user["company_id"]), customer_id, body.dict(exclude_unset=True)
    )


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    service: CustomerService = Depends(_get_customer_service),
):
    """Soft-delete (deactivate) a customer."""
    await service.delete_customer(str(current_user["company_id"]), customer_id)
