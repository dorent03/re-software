"""PDF generation using WeasyPrint and Jinja2 HTML templates with SEPA QR support."""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.core.config import settings
from app.models.document import DocumentType
from app.utils.sepa_qr import generate_sepa_qr_image

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)

DOCUMENT_TITLE_MAP = {
    DocumentType.INVOICE: "Rechnung",
    DocumentType.QUOTE: "Angebot",
    DocumentType.DELIVERY_NOTE: "Lieferschein",
    DocumentType.ORDER_CONFIRMATION: "Auftragsbestätigung",
    DocumentType.PARTIAL_INVOICE: "Abschlagsrechnung",
    DocumentType.CREDIT_NOTE: "Gutschrift",
    DocumentType.CANCELLATION: "Stornorechnung",
}


def _build_vat_breakdown(items: list, is_kleinunternehmer: bool) -> list:
    """Group items by VAT rate and sum net / vat amounts for the breakdown table."""
    if is_kleinunternehmer:
        return []

    groups: Dict[float, Dict[str, float]] = defaultdict(lambda: {"net": 0.0, "vat": 0.0})
    for item in items:
        rate = item.get("vat_rate", 0)
        groups[rate]["net"] += abs(item.get("net_amount", 0))
        groups[rate]["vat"] += abs(item.get("vat_amount", 0))

    breakdown = []
    for rate in sorted(groups.keys(), reverse=True):
        breakdown.append({
            "rate": rate,
            "rate_pct": f"{rate * 100:.0f}",
            "net": round(groups[rate]["net"], 2),
            "vat": round(groups[rate]["vat"], 2),
        })
    return breakdown


async def generate_document_pdf(
    document: Dict[str, Any],
    company: Dict[str, Any],
    customer: Dict[str, Any],
    related_document_number: str = "",
) -> str:
    """Render a document as a PDF with QR code, discounts, and VAT breakdown."""
    document_title = DOCUMENT_TITLE_MAP.get(
        document.get("document_type", ""), "Dokument"
    )

    # Resolve logo absolute path
    logo_path = company.get("logo_path", "")
    if logo_path:
        abs_logo = settings.UPLOAD_DIR.parent / logo_path
        if abs_logo.exists():
            logo_path = abs_logo.as_uri()
        else:
            logo_path = ""
    company_ctx = {**company, "logo_path": logo_path}

    # Generate SEPA QR code image
    qr_path = ""
    if document.get("document_type") in (
        DocumentType.INVOICE, DocumentType.PARTIAL_INVOICE
    ):
        qr_file = generate_sepa_qr_image(document, company)
        if qr_file:
            qr_path = Path(qr_file).as_uri()

    # VAT breakdown
    is_klein = document.get("is_kleinunternehmer", False)
    vat_breakdown = _build_vat_breakdown(document.get("items", []), is_klein)

    # Check if any item has a discount
    has_discounts = any(item.get("discount_percent", 0) > 0 for item in document.get("items", []))

    template = jinja_env.get_template("invoice.html")
    html_content = template.render(
        document=document,
        line_items=document.get("items", []),
        company=company_ctx,
        customer=customer,
        document_title=document_title,
        qr_path=qr_path,
        vat_breakdown=vat_breakdown,
        has_discounts=has_discounts,
        related_document_number=related_document_number,
    )

    pdf_filename = f"{document['document_number']}.pdf"
    pdf_path = settings.PDF_DIR / pdf_filename

    html_obj = HTML(string=html_content, base_url=str(settings.UPLOAD_DIR.parent))
    html_obj.write_pdf(str(pdf_path))

    relative_path = f"pdfs/{pdf_filename}"
    logger.info("Generated PDF: %s", relative_path)
    return relative_path
