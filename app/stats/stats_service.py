"""Statistics service using MongoDB aggregation pipelines."""

import logging
from typing import Any, Dict, List

from app.repositories.customer_repository import CustomerRepository
from app.repositories.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


class StatsService:
    """Aggregation-based revenue statistics."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        customer_repo: CustomerRepository,
    ):
        self.document_repo = document_repo
        self.customer_repo = customer_repo

    async def monthly_revenue(self, company_id: str) -> List[Dict[str, Any]]:
        """Sum gross totals of PAID invoices grouped by month."""
        results = await self.document_repo.aggregate_monthly_revenue(company_id)
        logger.info("Monthly revenue aggregation for company %s: %d periods", company_id, len(results))
        return results

    async def revenue_by_customer(self, company_id: str) -> List[Dict[str, Any]]:
        """Sum gross totals of PAID invoices grouped by customer."""
        results = await self.document_repo.aggregate_revenue_by_customer(company_id)

        # Enrich with customer names
        for entry in results:
            customer = await self.customer_repo.find_by_id(entry["customer_id"])
            entry["customer_name"] = customer.get("name", "Unknown") if customer else "Unknown"

        logger.info("Customer revenue aggregation for company %s: %d customers", company_id, len(results))
        return results
