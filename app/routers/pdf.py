"""PDF generation and preview routes."""

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.repositories.company_repository import CompanyRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.document_repository import DocumentRepository
from app.services.pdf_service import PDFService

router = APIRouter(prefix="/documents", tags=["PDF"])


def _get_pdf_service(db=Depends(get_database)) -> PDFService:
    return PDFService(
        document_repo=DocumentRepository(db),
        company_repo=CompanyRepository(db),
        customer_repo=CustomerRepository(db),
    )


@router.post("/{document_id}/pdf")
async def generate_pdf(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    service: PDFService = Depends(_get_pdf_service),
):
    """Generate a PDF for the specified document."""
    return await service.generate_pdf(
        str(current_user["company_id"]), document_id
    )


@router.get("/{document_id}/pdf/preview")
async def preview_pdf(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    service: PDFService = Depends(_get_pdf_service),
):
    """Return the PDF file for inline preview (Content-Disposition: inline)."""
    abs_path = await service.get_pdf_path(
        str(current_user["company_id"]), document_id
    )
    return FileResponse(
        path=str(abs_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={abs_path.name}"},
    )


@router.get("/{document_id}/pdf/download")
async def download_pdf(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    service: PDFService = Depends(_get_pdf_service),
):
    """Download the PDF file as an attachment."""
    abs_path = await service.get_pdf_path(
        str(current_user["company_id"]), document_id
    )
    return FileResponse(
        path=str(abs_path),
        media_type="application/pdf",
        filename=abs_path.name,
    )
