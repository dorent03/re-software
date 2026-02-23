"""Statistics API routes."""

from fastapi import APIRouter, Depends

from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.repositories.customer_repository import CustomerRepository
from app.repositories.document_repository import DocumentRepository
from app.stats.stats_service import StatsService

router = APIRouter(prefix="/stats", tags=["Statistics"])


def _get_stats_service(db=Depends(get_database)) -> StatsService:
    return StatsService(
        document_repo=DocumentRepository(db),
        customer_repo=CustomerRepository(db),
    )


@router.get("/revenue/monthly")
async def monthly_revenue(
    current_user: dict = Depends(get_current_user),
    service: StatsService = Depends(_get_stats_service),
):
    """Sum gross totals of PAID invoices grouped by year and month."""
    data = await service.monthly_revenue(str(current_user["company_id"]))
    return {"data": data}


@router.get("/revenue/by-customer")
async def revenue_by_customer(
    current_user: dict = Depends(get_current_user),
    service: StatsService = Depends(_get_stats_service),
):
    """Sum gross totals of PAID invoices grouped by customer."""
    data = await service.revenue_by_customer(str(current_user["company_id"]))
    return {"data": data}
