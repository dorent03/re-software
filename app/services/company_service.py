"""Company service for company profile management."""

import logging
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.repositories.company_repository import CompanyRepository

logger = logging.getLogger(__name__)


class CompanyService:
    """Business logic for company operations."""

    def __init__(self, company_repo: CompanyRepository):
        self.company_repo = company_repo

    async def get_company(self, company_id: str) -> Dict[str, Any]:
        """Retrieve a company by ID."""
        company = await self.company_repo.find_by_id(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )
        return company

    async def update_company(
        self, company_id: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update company profile fields."""
        # Remove None values
        filtered = {k: v for k, v in update_data.items() if v is not None}
        if not filtered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        updated = await self.company_repo.update_one(company_id, filtered)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )

        logger.info("Updated company %s", company_id)
        return updated

    async def upload_logo(self, company_id: str, file: UploadFile) -> Dict[str, Any]:
        """Save an uploaded logo file and store its path on the company."""
        allowed_types = {"image/png", "image/jpeg", "image/svg+xml", "image/webp"}
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Accepted: {', '.join(allowed_types)}",
            )

        logo_dir = settings.UPLOAD_DIR / "logos"
        logo_dir.mkdir(parents=True, exist_ok=True)

        extension = Path(file.filename).suffix if file.filename else ".png"
        filename = f"{company_id}{extension}"
        file_path = logo_dir / filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        relative_path = f"uploads/logos/{filename}"
        updated = await self.company_repo.update_one(
            company_id, {"logo_path": relative_path}
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )

        logger.info("Uploaded logo for company %s", company_id)
        return updated
