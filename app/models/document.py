"""Document database model shape definition — supports invoices, quotes,
delivery notes, order confirmations, partial invoices, credit notes, cancellations."""


class DocumentType:
    INVOICE = "INVOICE"
    QUOTE = "QUOTE"
    DELIVERY_NOTE = "DELIVERY_NOTE"
    ORDER_CONFIRMATION = "ORDER_CONFIRMATION"
    PARTIAL_INVOICE = "PARTIAL_INVOICE"
    CREDIT_NOTE = "CREDIT_NOTE"
    CANCELLATION = "CANCELLATION"

    ALL = [
        INVOICE, QUOTE, DELIVERY_NOTE, ORDER_CONFIRMATION,
        PARTIAL_INVOICE, CREDIT_NOTE, CANCELLATION,
    ]

    # Types that use sequential invoice-style numbering
    NUMBERED_TYPES = [INVOICE, PARTIAL_INVOICE, CREDIT_NOTE, CANCELLATION]


class DocumentStatus:
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    CANCELLED = "CANCELLED"
    OVERDUE = "OVERDUE"
    # Quote-specific
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CONVERTED = "CONVERTED"

    INVOICE_STATUSES = [DRAFT, SENT, PARTIALLY_PAID, PAID, CANCELLED, OVERDUE]
    QUOTE_STATUSES = [DRAFT, SENT, ACCEPTED, REJECTED, CANCELLED, CONVERTED]

    ALL = list(set(INVOICE_STATUSES + QUOTE_STATUSES))


class PaymentMethod:
    BANK = "BANK"
    CASH = "CASH"
    PAYPAL = "PAYPAL"

    ALL = [BANK, CASH, PAYPAL]


DOCUMENT_NUMBER_PREFIX = {
    DocumentType.INVOICE: "INV",
    DocumentType.QUOTE: "QUO",
    DocumentType.DELIVERY_NOTE: "LS",
    DocumentType.ORDER_CONFIRMATION: "AB",
    DocumentType.PARTIAL_INVOICE: "TINV",
    DocumentType.CREDIT_NOTE: "GS",
    DocumentType.CANCELLATION: "ST",
}


def new_line_item(
    product_id: str,
    name: str,
    description: str,
    quantity: float,
    unit: str,
    unit_price: float,
    vat_rate: float,
    discount_percent: float = 0.0,
) -> dict:
    """Return a dict for a single line item with discount support."""
    subtotal = round(quantity * unit_price, 2)
    discount_amount = round(subtotal * (discount_percent / 100.0), 2)
    net_amount = round(subtotal - discount_amount, 2)
    vat_amount = round(net_amount * vat_rate, 2)
    gross_amount = round(net_amount + vat_amount, 2)
    return {
        "product_id": product_id,
        "name": name,
        "description": description,
        "quantity": quantity,
        "unit": unit,
        "unit_price": unit_price,
        "vat_rate": vat_rate,
        "discount_percent": discount_percent,
        "discount_amount": discount_amount,
        "net_amount": net_amount,
        "vat_amount": vat_amount,
        "gross_amount": gross_amount,
    }


def new_document(
    company_id: str,
    customer_id: str,
    document_type: str,
    document_number: str,
    items: list,
    is_kleinunternehmer: bool = False,
    notes: str = "",
    payment_terms_days: int = 14,
    issue_date: str = "",
    service_date: str = "",
    due_date: str = "",
    pdf_path: str = "",
    related_document_id: str = "",
) -> dict:
    """Return a dict representing a new document for MongoDB insertion."""
    from app.utils.helpers import now_utc

    total_net = round(sum(item["net_amount"] for item in items), 2)
    total_vat = 0.0 if is_kleinunternehmer else round(sum(item["vat_amount"] for item in items), 2)
    total_gross = round(total_net + total_vat, 2)

    # If Kleinunternehmer, zero out VAT on each line item
    if is_kleinunternehmer:
        for item in items:
            item["vat_amount"] = 0.0
            item["gross_amount"] = item["net_amount"]

    # Credit notes and cancellations store negative totals
    if document_type in (DocumentType.CREDIT_NOTE, DocumentType.CANCELLATION):
        total_net = -abs(total_net)
        total_vat = -abs(total_vat)
        total_gross = -abs(total_gross)

    return {
        "company_id": company_id,
        "customer_id": customer_id,
        "document_type": document_type,
        "document_number": document_number,
        "status": DocumentStatus.DRAFT,
        "items": items,
        "totals": {
            "net": total_net,
            "vat": total_vat,
            "gross": total_gross,
            "paid_amount": 0.0,
            "remaining_amount": total_gross,
        },
        "payments": [],
        "reminders": [],
        "is_kleinunternehmer": is_kleinunternehmer,
        "notes": notes,
        "payment_terms_days": payment_terms_days,
        "issue_date": issue_date,
        "service_date": service_date,
        "due_date": due_date,
        "pdf_path": pdf_path,
        "related_document_id": related_document_id,
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
