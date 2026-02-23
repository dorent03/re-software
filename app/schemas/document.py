"""Document (Invoice / Quote / etc.) request/response schemas."""

from pydantic import BaseModel, Field, validator
from typing import List, Optional

from app.core.config import settings
from app.models.document import DocumentType, DocumentStatus, PaymentMethod


class LineItemCreate(BaseModel):
    product_id: Optional[str] = Field(None, description="Product ID reference (optional for free-text items)")
    quantity: float = Field(..., gt=0, description="Quantity of product")
    discount_percent: float = Field(default=0.0, ge=0, le=100, description="Discount percentage")
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    unit: Optional[str] = Field(None, max_length=50)
    unit_price: Optional[float] = Field(None, gt=0)
    vat_rate: Optional[float] = None

    @validator("vat_rate")
    def validate_vat_rate(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value not in settings.ALLOWED_VAT_RATES:
            raise ValueError(f"VAT rate must be one of {settings.ALLOWED_VAT_RATES}")
        return value


class LineItemResponse(BaseModel):
    product_id: str = ""
    name: str = ""
    description: str = ""
    quantity: float = 0.0
    unit: str = "Stück"
    unit_price: float = 0.0
    vat_rate: float = 0.19
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    net_amount: float = 0.0
    vat_amount: float = 0.0
    gross_amount: float = 0.0

    def __init__(self, **data):
        for field in ("product_id", "name", "description", "unit"):
            if data.get(field) is None:
                data[field] = ""
        super().__init__(**data)


class TotalsResponse(BaseModel):
    net: float = 0.0
    vat: float = 0.0
    gross: float = 0.0
    paid_amount: float = 0.0
    remaining_amount: float = 0.0


class PaymentRecord(BaseModel):
    amount: float = 0.0
    date: str = ""
    method: str = ""
    reference: str = ""

    def __init__(self, **data):
        for field in ("date", "method", "reference"):
            if data.get(field) is None:
                data[field] = ""
        super().__init__(**data)


class ReminderRecord(BaseModel):
    level: int = 1
    date: str = ""
    fee: float = 0.0

    def __init__(self, **data):
        if data.get("date") is None:
            data["date"] = ""
        super().__init__(**data)


class DocumentCreate(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    document_type: str = Field(..., description="Document type")
    items: List[LineItemCreate] = Field(..., min_items=1, description="Line items")
    notes: Optional[str] = Field(None, max_length=2000)
    payment_terms_days: int = Field(default=14, ge=0, le=365)
    issue_date: Optional[str] = Field(None, description="ISO date string YYYY-MM-DD")
    service_date: Optional[str] = Field(None, description="Service/delivery date YYYY-MM-DD")
    due_date: Optional[str] = Field(None, description="ISO date string YYYY-MM-DD")
    related_document_id: Optional[str] = Field(None, description="Related document ID")

    @validator("document_type")
    def validate_document_type(cls, value: str) -> str:
        if value not in DocumentType.ALL:
            raise ValueError(f"document_type must be one of {DocumentType.ALL}")
        return value


class DocumentUpdate(BaseModel):
    """Allowed updates on a draft document."""
    customer_id: Optional[str] = None
    items: Optional[List[LineItemCreate]] = None
    notes: Optional[str] = Field(None, max_length=2000)
    payment_terms_days: Optional[int] = Field(None, ge=0, le=365)
    issue_date: Optional[str] = None
    service_date: Optional[str] = None
    due_date: Optional[str] = None


class DocumentStatusUpdate(BaseModel):
    status: str = Field(..., description="New status")

    @validator("status")
    def validate_status(cls, value: str) -> str:
        if value not in DocumentStatus.ALL:
            raise ValueError(f"status must be one of {DocumentStatus.ALL}")
        return value


class PaymentCreate(BaseModel):
    """Record a payment against an invoice."""
    amount: float = Field(..., gt=0, description="Payment amount in EUR")
    date: Optional[str] = Field(None, description="Payment date YYYY-MM-DD")
    method: str = Field(default="BANK", description="Payment method")

    @validator("method")
    def validate_method(cls, value: str) -> str:
        if value not in PaymentMethod.ALL:
            raise ValueError(f"method must be one of {PaymentMethod.ALL}")
        return value


class ReminderCreate(BaseModel):
    """Create a reminder (Mahnung) for an overdue invoice."""
    fee: float = Field(default=0.0, ge=0, description="Reminder fee in EUR")


class ConvertQuoteRequest(BaseModel):
    """Convert an accepted quote to an invoice."""
    payment_terms_days: int = Field(default=14, ge=0, le=365)
    issue_date: Optional[str] = None
    due_date: Optional[str] = None


class CreatePartialRequest(BaseModel):
    """Create a partial invoice (Abschlagsrechnung) from an existing invoice."""
    amount: float = Field(..., gt=0, description="Partial invoice amount (gross)")
    items: Optional[List[LineItemCreate]] = Field(None, description="Custom line items (optional, derived from amount if omitted)")
    notes: str = Field(default="", max_length=2000)
    payment_terms_days: int = Field(default=14, ge=0, le=365)


class DocumentResponse(BaseModel):
    id: str
    company_id: str = ""
    customer_id: str = ""
    document_type: str = ""
    document_number: str = ""
    status: str = ""
    items: List[LineItemResponse] = []
    totals: TotalsResponse = TotalsResponse()
    payments: List[PaymentRecord] = []
    reminders: List[ReminderRecord] = []
    is_kleinunternehmer: bool = False
    notes: str = ""
    payment_terms_days: int = 14
    issue_date: str = ""
    service_date: str = ""
    due_date: str = ""
    pdf_path: str = ""
    related_document_id: str = ""
    created_at: str = ""
    updated_at: str = ""

    class Config:
        orm_mode = True

    def __init__(self, **data):
        str_fields = (
            "company_id", "customer_id", "document_type", "document_number",
            "status", "notes", "issue_date", "service_date", "due_date",
            "pdf_path", "related_document_id", "created_at", "updated_at",
        )
        for field in str_fields:
            if data.get(field) is None:
                data[field] = ""
        super().__init__(**data)


class PaginatedDocumentResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
