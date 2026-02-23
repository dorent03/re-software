"""Document routes — CRUD, payments, reminders, cancel, credit, convert, e-invoice."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.repositories.company_repository import CompanyRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.document_repository import CounterRepository, DocumentRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.document import (
    ConvertQuoteRequest,
    CreatePartialRequest,
    DocumentCreate,
    DocumentResponse,
    DocumentStatusUpdate,
    DocumentUpdate,
    PaymentCreate,
    ReminderCreate,
)
from app.services.document_service import DocumentService
from app.services.einvoice_service import EInvoiceService

router = APIRouter(prefix="/documents", tags=["Documents"])


def _get_document_service(db=Depends(get_database)) -> DocumentService:
    return DocumentService(
        document_repo=DocumentRepository(db),
        counter_repo=CounterRepository(db),
        product_repo=ProductRepository(db),
        customer_repo=CustomerRepository(db),
        company_repo=CompanyRepository(db),
    )


def _get_einvoice_service(db=Depends(get_database)) -> EInvoiceService:
    return EInvoiceService(
        document_repo=DocumentRepository(db),
        company_repo=CompanyRepository(db),
        customer_repo=CustomerRepository(db),
    )


# ------------------------------------------------------------------
# CRUD
# ------------------------------------------------------------------

@router.post("/", response_model=DocumentResponse, status_code=201)
async def create_document(
    body: DocumentCreate,
    current_user: dict = Depends(get_current_user),
    service: DocumentService = Depends(_get_document_service),
):
    """Create a new document (invoice, quote, delivery note, etc.)."""
    return await service.create_document(
        str(current_user["company_id"]), body.dict()
    )


@router.get("/")
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=100),
    document_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    service: DocumentService = Depends(_get_document_service),
):
    """List documents with pagination and filters."""
    return await service.list_documents(
        company_id=str(current_user["company_id"]),
        page=page,
        page_size=page_size,
        search=search,
        document_type=document_type,
        document_status=status,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    service: DocumentService = Depends(_get_document_service),
):
    """Retrieve a single document."""
    return await service.get_document(
        str(current_user["company_id"]), document_id
    )


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    body: DocumentUpdate,
    current_user: dict = Depends(get_current_user),
    service: DocumentService = Depends(_get_document_service),
):
    """Update a draft document."""
    return await service.update_document(
        str(current_user["company_id"]), document_id, body.dict(exclude_unset=True)
    )


@router.patch("/{document_id}/status", response_model=DocumentResponse)
async def update_document_status(
    document_id: str,
    body: DocumentStatusUpdate,
    current_user: dict = Depends(get_current_user),
    service: DocumentService = Depends(_get_document_service),
):
    """Transition a document's status."""
    return await service.update_status(
        str(current_user["company_id"]), document_id, body.status
    )


# ------------------------------------------------------------------
# Related Documents
# ------------------------------------------------------------------

@router.get("/{document_id}/related")
async def get_related_documents(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    service: DocumentService = Depends(_get_document_service),
):
    """Retrieve parent and child documents linked to a document."""
    return await service.get_related_documents(
        str(current_user["company_id"]), document_id
    )


# ------------------------------------------------------------------
# Convert
# ------------------------------------------------------------------

@router.post("/{quote_id}/convert", response_model=DocumentResponse, status_code=201)
async def convert_quote_to_invoice(
    quote_id: str,
    body: Optional[ConvertQuoteRequest] = None,
    current_user: dict = Depends(get_current_user),
    service: DocumentService = Depends(_get_document_service),
):
    """Convert an accepted quote into a new invoice."""
    data = body.dict() if body else {}
    return await service.convert_quote_to_invoice(
        str(current_user["company_id"]), quote_id, data
    )


# ------------------------------------------------------------------
# Partial Invoice (Abschlagsrechnung)
# ------------------------------------------------------------------

@router.post("/{document_id}/create-partial", response_model=DocumentResponse, status_code=201)
async def create_partial_invoice(
    document_id: str,
    body: CreatePartialRequest,
    current_user: dict = Depends(get_current_user),
    service: DocumentService = Depends(_get_document_service),
):
    """Create a partial invoice (Abschlagsrechnung) from an existing invoice."""
    return await service.create_partial_invoice(
        str(current_user["company_id"]), document_id, body.dict()
    )


# ------------------------------------------------------------------
# Payments
# ------------------------------------------------------------------

@router.post("/{document_id}/payment", response_model=DocumentResponse, status_code=201)
async def add_payment(
    document_id: str,
    body: PaymentCreate,
    current_user: dict = Depends(get_current_user),
    service: DocumentService = Depends(_get_document_service),
):
    """Record a partial or full payment against an invoice."""
    return await service.add_payment(
        str(current_user["company_id"]), document_id, body.dict()
    )


# ------------------------------------------------------------------
# Reminders (Mahnwesen)
# ------------------------------------------------------------------

@router.post("/{document_id}/reminder", response_model=DocumentResponse, status_code=201)
async def add_reminder(
    document_id: str,
    body: ReminderCreate,
    current_user: dict = Depends(get_current_user),
    service: DocumentService = Depends(_get_document_service),
):
    """Create a reminder (Mahnung) for an overdue invoice."""
    return await service.add_reminder(
        str(current_user["company_id"]), document_id, body.dict()
    )


# ------------------------------------------------------------------
# Cancel + Credit
# ------------------------------------------------------------------

@router.post("/{document_id}/cancel", response_model=DocumentResponse, status_code=201)
async def cancel_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    service: DocumentService = Depends(_get_document_service),
):
    """Cancel an invoice and generate a cancellation document (Storno)."""
    return await service.cancel_document(
        str(current_user["company_id"]), document_id
    )


@router.post("/{document_id}/credit", response_model=DocumentResponse, status_code=201)
async def create_credit_note(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    service: DocumentService = Depends(_get_document_service),
):
    """Generate a credit note (Gutschrift) for an invoice."""
    return await service.create_credit_note(
        str(current_user["company_id"]), document_id
    )


# ------------------------------------------------------------------
# E-Invoice
# ------------------------------------------------------------------

@router.get("/{document_id}/xrechnung")
async def get_xrechnung(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    service: EInvoiceService = Depends(_get_einvoice_service),
):
    """Download XRechnung (UBL 2.1) XML."""
    xml_str = await service.generate_xrechnung(
        str(current_user["company_id"]), document_id
    )
    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=xrechnung_{document_id}.xml"},
    )


@router.get("/{document_id}/zugferd")
async def get_zugferd(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    service: EInvoiceService = Depends(_get_einvoice_service),
):
    """Download ZUGFeRD (CII) XML."""
    xml_str = await service.generate_zugferd(
        str(current_user["company_id"]), document_id
    )
    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=zugferd_{document_id}.xml"},
    )
