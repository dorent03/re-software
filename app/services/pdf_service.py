"""PDF service orchestrating document PDF generation and retrieval."""

import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import HTTPException, status

from app.core.config import settings
from app.pdf.generator import generate_document_pdf
from app.repositories.company_repository import CompanyRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


class PDFService:
    """Business logic for PDF generation and retrieval."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        company_repo: CompanyRepository,
        customer_repo: CustomerRepository,
    ):
        self.document_repo = document_repo
        self.company_repo = company_repo
        self.customer_repo = customer_repo

    async def generate_pdf(
        self, company_id: str, document_id: str
    ) -> Dict[str, Any]:
        """Generate a PDF for a document and store the file path."""
        document = await self.document_repo.find_by_id(document_id)
        if not document or document.get("company_id") != company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        company = await self.company_repo.find_by_id(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )

        customer = await self.customer_repo.find_by_id(document["customer_id"])
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        # Resolve related document number for PDF display
        related_doc_number = ""
        related_id = document.get("related_document_id", "")
        if related_id:
            related_doc = await self.document_repo.find_by_id(related_id)
            if related_doc:
                related_doc_number = related_doc.get("document_number", "")

        pdf_path = await generate_document_pdf(
            document, company, customer, related_document_number=related_doc_number,
        )

        # Store path on the document
        await self.document_repo.update_one(document_id, {"pdf_path": pdf_path})

        logger.info("Generated PDF for document %s", document_id)
        return {"pdf_path": pdf_path, "document_id": document_id}

    async def get_pdf_path(self, company_id: str, document_id: str) -> Path:
        """Return the absolute filesystem path to a generated PDF."""
        document = await self.document_repo.find_by_id(document_id)
        if not document or document.get("company_id") != company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        pdf_path = document.get("pdf_path", "")
        if not pdf_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF has not been generated yet. Generate it first.",
            )

        abs_path = settings.PDF_DIR.parent / pdf_path
        if not abs_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF file not found on disk",
            )

        return abs_path
