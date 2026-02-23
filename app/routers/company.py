"""Company profile routes."""

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.repositories.company_repository import CompanyRepository
from app.schemas.company import CompanyResponse, CompanyUpdate
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["Companies"])


def _get_company_service(db=Depends(get_database)) -> CompanyService:
    return CompanyService(company_repo=CompanyRepository(db))


@router.get("/me", response_model=CompanyResponse)
async def get_my_company(
    current_user: dict = Depends(get_current_user),
    service: CompanyService = Depends(_get_company_service),
):
    """Retrieve the authenticated user's company profile."""
    return await service.get_company(str(current_user["company_id"]))


@router.patch("/me", response_model=CompanyResponse)
async def update_my_company(
    body: CompanyUpdate,
    current_user: dict = Depends(get_current_user),
    service: CompanyService = Depends(_get_company_service),
):
    """Update the authenticated user's company profile."""
    return await service.update_company(
        str(current_user["company_id"]), body.dict(exclude_unset=True)
    )


@router.post("/me/logo", response_model=CompanyResponse)
async def upload_company_logo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    service: CompanyService = Depends(_get_company_service),
):
    """Upload a company logo image."""
    return await service.upload_logo(str(current_user["company_id"]), file)
