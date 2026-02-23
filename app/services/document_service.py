"""Document service — full business logic for invoices, quotes, payments,
reminders, credit notes, cancellations, and partial invoices."""

import copy
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from app.core.config import settings
from app.models.document import (
    DOCUMENT_NUMBER_PREFIX,
    DocumentStatus,
    DocumentType,
    new_document,
    new_line_item,
)
from app.repositories.company_repository import CompanyRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.document_repository import CounterRepository, DocumentRepository
from app.repositories.product_repository import ProductRepository
from app.utils.pagination import (
    build_filter_query,
    build_paginated_response,
    build_pagination_query,
)

logger = logging.getLogger(__name__)

DOCUMENT_SEARCH_FIELDS = ["document_number", "notes"]


class DocumentService:
    """Business logic for all document operations."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        counter_repo: CounterRepository,
        product_repo: ProductRepository,
        customer_repo: CustomerRepository,
        company_repo: CompanyRepository,
    ):
        self.document_repo = document_repo
        self.counter_repo = counter_repo
        self.product_repo = product_repo
        self.customer_repo = customer_repo
        self.company_repo = company_repo

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_document(
        self, company_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new document with server-calculated totals."""
        document_type = data["document_type"]
        customer_id = data["customer_id"]

        customer = await self.customer_repo.find_by_id(customer_id)
        if not customer or customer.get("company_id") != company_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

        company = await self.company_repo.find_by_id(company_id)
        is_kleinunternehmer = company.get("is_kleinunternehmer", False) if company else False

        resolved_items = await self._resolve_line_items(company_id, data["items"], is_kleinunternehmer)
        document_number = await self._generate_document_number(company_id, document_type)

        issue_date = data.get("issue_date") or datetime.utcnow().strftime("%Y-%m-%d")
        service_date = data.get("service_date") or ""
        payment_terms_days = data.get("payment_terms_days", 14)
        due_date = data.get("due_date") or self._calc_due_date(issue_date, payment_terms_days)

        doc = new_document(
            company_id=company_id,
            customer_id=customer_id,
            document_type=document_type,
            document_number=document_number,
            items=resolved_items,
            is_kleinunternehmer=is_kleinunternehmer,
            notes=data.get("notes", ""),
            payment_terms_days=payment_terms_days,
            issue_date=issue_date,
            service_date=service_date,
            due_date=due_date,
            related_document_id=data.get("related_document_id", ""),
        )
        doc_id = await self.document_repo.insert_one(doc)
        logger.info("Created %s %s for company %s", document_type, document_number, company_id)
        created = await self.document_repo.find_by_id(doc_id)
        return self._serialize_dates(created)

    async def get_document(self, company_id: str, document_id: str) -> Dict[str, Any]:
        """Retrieve a single document, enforcing tenant isolation."""
        doc = await self.document_repo.find_by_id(document_id)
        if not doc or doc.get("company_id") != company_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return self._serialize_dates(doc)

    async def list_documents(
        self,
        company_id: str,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        document_type: Optional[str] = None,
        document_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List documents with pagination and filters."""
        extra_filters: Dict[str, Any] = {}
        if document_type:
            extra_filters["document_type"] = document_type
        if document_status:
            extra_filters["status"] = document_status

        query = build_filter_query(
            company_id=company_id,
            search=search,
            search_fields=DOCUMENT_SEARCH_FIELDS,
            extra_filters=extra_filters,
        )
        pag = build_pagination_query(page, page_size)
        items = await self.document_repo.find_many(query, **pag)
        total = await self.document_repo.count(query)
        serialized = [self._serialize_dates(item) for item in items]
        return build_paginated_response(serialized, total, page, page_size)

    async def update_document(
        self, company_id: str, document_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a draft document's editable fields."""
        doc = await self.get_document(company_id, document_id)
        if doc["status"] != DocumentStatus.DRAFT:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only DRAFT documents can be edited")

        update_fields: Dict[str, Any] = {}

        if data.get("items") is not None:
            company = await self.company_repo.find_by_id(company_id)
            is_klein = company.get("is_kleinunternehmer", False) if company else False
            resolved = await self._resolve_line_items(company_id, data["items"], is_klein)
            update_fields["items"] = resolved
            totals = self._calc_totals(resolved, is_klein, doc["document_type"])
            update_fields["totals"] = totals

        for field in ["customer_id", "notes", "payment_terms_days", "issue_date", "service_date", "due_date"]:
            if data.get(field) is not None:
                update_fields[field] = data[field]

        if not update_fields:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

        updated = await self.document_repo.update_one(document_id, update_fields)
        logger.info("Updated document %s", document_id)
        return self._serialize_dates(updated)

    async def update_status(
        self, company_id: str, document_id: str, new_status: str
    ) -> Dict[str, Any]:
        """Transition a document's status with validation rules."""
        doc = await self.get_document(company_id, document_id)
        self._validate_status_transition(doc["document_type"], doc["status"], new_status)
        updated = await self.document_repo.update_one(document_id, {"status": new_status})

        # When a quote is accepted, create an order confirmation (Auftragsbestätigung) from it
        if (
            doc["document_type"] == DocumentType.QUOTE
            and new_status == DocumentStatus.ACCEPTED
        ):
            await self._create_order_confirmation_from_quote(company_id, document_id, updated)

        logger.info("Document %s status: %s -> %s", document_id, doc["status"], new_status)
        return self._serialize_dates(updated)

    async def convert_quote_to_invoice(
        self, company_id: str, quote_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert an accepted quote into a new invoice."""
        quote = await self.get_document(company_id, quote_id)

        if quote["document_type"] != DocumentType.QUOTE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only quotes can be converted")
        if quote["status"] != DocumentStatus.ACCEPTED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only accepted quotes can be converted")

        invoice_number = await self._generate_document_number(company_id, DocumentType.INVOICE)
        issue_date = data.get("issue_date") or datetime.utcnow().strftime("%Y-%m-%d")
        payment_terms_days = data.get("payment_terms_days", 14)
        due_date = data.get("due_date") or self._calc_due_date(issue_date, payment_terms_days)

        invoice_doc = new_document(
            company_id=company_id,
            customer_id=quote["customer_id"],
            document_type=DocumentType.INVOICE,
            document_number=invoice_number,
            items=quote["items"],
            is_kleinunternehmer=quote.get("is_kleinunternehmer", False),
            notes=quote.get("notes", ""),
            payment_terms_days=payment_terms_days,
            issue_date=issue_date,
            due_date=due_date,
            related_document_id=quote_id,
        )
        invoice_id = await self.document_repo.insert_one(invoice_doc)

        # Mark the original quote as CONVERTED
        await self.document_repo.update_one(quote_id, {"status": DocumentStatus.CONVERTED})

        logger.info("Converted quote %s to invoice %s", quote_id, invoice_id)
        created = await self.document_repo.find_by_id(invoice_id)
        return self._serialize_dates(created)

    async def _create_order_confirmation_from_quote(
        self, company_id: str, quote_id: str, quote: Dict[str, Any]
    ) -> None:
        """Create an ORDER_CONFIRMATION document from an accepted quote."""
        items_copy = copy.deepcopy(quote.get("items", []))
        order_number = await self._generate_document_number(company_id, DocumentType.ORDER_CONFIRMATION)
        issue_date = quote.get("issue_date") or datetime.utcnow().strftime("%Y-%m-%d")
        service_date = quote.get("service_date", "")
        payment_terms_days = quote.get("payment_terms_days", 14)
        due_date = quote.get("due_date") or self._calc_due_date(issue_date, payment_terms_days)

        order_doc = new_document(
            company_id=company_id,
            customer_id=quote["customer_id"],
            document_type=DocumentType.ORDER_CONFIRMATION,
            document_number=order_number,
            items=items_copy,
            is_kleinunternehmer=quote.get("is_kleinunternehmer", False),
            notes=f"Auftragsbestätigung zu Angebot {quote.get('document_number', '')}",
            payment_terms_days=payment_terms_days,
            issue_date=issue_date,
            service_date=service_date,
            due_date=due_date,
            related_document_id=quote_id,
        )
        await self.document_repo.insert_one(order_doc)
        logger.info("Created order confirmation from quote %s", quote_id)

    # ------------------------------------------------------------------
    # PAYMENTS (Teilzahlungen)
    # ------------------------------------------------------------------

    async def add_payment(
        self, company_id: str, document_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record a payment against an invoice. Adjusts status automatically."""
        doc = await self.get_document(company_id, document_id)

        if doc["document_type"] not in (DocumentType.INVOICE, DocumentType.PARTIAL_INVOICE):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payments only allowed on invoices")

        if doc["status"] in (DocumentStatus.CANCELLED, DocumentStatus.PAID, DocumentStatus.DRAFT):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add payment to a {doc['status']} document",
            )

        totals = doc.get("totals", {})
        remaining = totals.get("remaining_amount", totals.get("gross", 0))
        amount = data["amount"]

        if amount > remaining + 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount {amount} exceeds remaining {remaining}",
            )

        payment_date = data.get("date") or datetime.utcnow().strftime("%Y-%m-%d")
        payment_record = {
            "amount": amount,
            "date": payment_date,
            "method": data.get("method", "BANK"),
        }

        updated = await self.document_repo.add_payment(document_id, payment_record)

        # Determine new status based on paid amount
        new_paid = updated["totals"]["paid_amount"]
        gross = abs(updated["totals"]["gross"])

        if abs(new_paid - gross) < 0.01:
            new_status = DocumentStatus.PAID
        elif new_paid > 0:
            new_status = DocumentStatus.PARTIALLY_PAID
        else:
            new_status = updated["status"]

        if new_status != updated["status"]:
            updated = await self.document_repo.update_one(document_id, {"status": new_status})

        # When a partial invoice becomes PAID, add the same amount as a payment on the parent invoice
        if (
            updated["document_type"] == DocumentType.PARTIAL_INVOICE
            and new_status == DocumentStatus.PAID
            and updated.get("related_document_id")
        ):
            parent_id = updated["related_document_id"]
            try:
                parent = await self.get_document(company_id, parent_id)
                if parent and parent.get("document_type") == DocumentType.INVOICE:
                    partial_gross = abs(updated["totals"]["gross"])
                    parent_payment = {
                        "amount": partial_gross,
                        "date": payment_date,
                        "method": data.get("method", "BANK"),
                        "reference": f"Abschlagsrechnung {updated.get('document_number', '')}",
                    }
                    parent_updated = await self.document_repo.add_payment(parent_id, parent_payment)
                    # Update parent status (PAID or PARTIALLY_PAID)
                    parent_paid = parent_updated["totals"]["paid_amount"]
                    parent_gross = abs(parent_updated["totals"]["gross"])
                    if abs(parent_paid - parent_gross) < 0.01:
                        await self.document_repo.update_one(parent_id, {"status": DocumentStatus.PAID})
                    elif parent_paid > 0:
                        await self.document_repo.update_one(parent_id, {"status": DocumentStatus.PARTIALLY_PAID})
                    logger.info(
                        "Synced partial payment %.2f to parent invoice %s",
                        partial_gross,
                        parent_id,
                    )
            except HTTPException:
                pass

        logger.info("Payment of %.2f recorded on document %s", amount, document_id)
        return self._serialize_dates(updated)

    # ------------------------------------------------------------------
    # REMINDERS (Mahnwesen)
    # ------------------------------------------------------------------

    async def add_reminder(
        self, company_id: str, document_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a reminder (Mahnung) for an overdue invoice."""
        doc = await self.get_document(company_id, document_id)

        if doc["document_type"] not in (DocumentType.INVOICE, DocumentType.PARTIAL_INVOICE):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reminders only for invoices")

        if doc["status"] not in (DocumentStatus.SENT, DocumentStatus.OVERDUE, DocumentStatus.PARTIALLY_PAID):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add reminder to a {doc['status']} invoice",
            )

        existing_reminders = doc.get("reminders", [])
        next_level = len(existing_reminders) + 1

        if next_level > settings.MAX_REMINDER_LEVEL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum reminder level {settings.MAX_REMINDER_LEVEL} reached",
            )

        reminder_record = {
            "level": next_level,
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "fee": data.get("fee", 0.0),
        }

        updated = await self.document_repo.add_reminder(document_id, reminder_record)

        # Transition to OVERDUE if not already
        if updated["status"] not in (DocumentStatus.OVERDUE, DocumentStatus.PARTIALLY_PAID):
            updated = await self.document_repo.update_one(document_id, {"status": DocumentStatus.OVERDUE})

        logger.info("Reminder level %d added to document %s", next_level, document_id)
        return self._serialize_dates(updated)

    # ------------------------------------------------------------------
    # CANCELLATION (Stornierung)
    # ------------------------------------------------------------------

    async def cancel_document(
        self, company_id: str, document_id: str
    ) -> Dict[str, Any]:
        """Cancel an invoice and generate a CANCELLATION document with negative totals."""
        doc = await self.get_document(company_id, document_id)

        if doc["document_type"] not in (DocumentType.INVOICE, DocumentType.PARTIAL_INVOICE):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only invoices can be cancelled")

        if doc["status"] == DocumentStatus.CANCELLED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document already cancelled")

        # Mark original as CANCELLED
        await self.document_repo.update_one(document_id, {"status": DocumentStatus.CANCELLED})

        # Generate cancellation document
        cancel_number = await self._generate_document_number(company_id, DocumentType.CANCELLATION)
        cancel_doc = new_document(
            company_id=company_id,
            customer_id=doc["customer_id"],
            document_type=DocumentType.CANCELLATION,
            document_number=cancel_number,
            items=doc["items"],
            is_kleinunternehmer=doc.get("is_kleinunternehmer", False),
            notes=f"Stornierung zu {doc['document_number']}",
            issue_date=datetime.utcnow().strftime("%Y-%m-%d"),
            due_date=datetime.utcnow().strftime("%Y-%m-%d"),
            related_document_id=document_id,
        )
        cancel_id = await self.document_repo.insert_one(cancel_doc)
        logger.info("Cancelled document %s, cancellation doc %s", document_id, cancel_id)
        created = await self.document_repo.find_by_id(cancel_id)
        return self._serialize_dates(created)

    # ------------------------------------------------------------------
    # CREDIT NOTE (Gutschrift)
    # ------------------------------------------------------------------

    async def create_credit_note(
        self, company_id: str, document_id: str
    ) -> Dict[str, Any]:
        """Generate a CREDIT_NOTE linked to an existing invoice."""
        doc = await self.get_document(company_id, document_id)

        if doc["document_type"] not in (DocumentType.INVOICE, DocumentType.PARTIAL_INVOICE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credit notes can only reference invoices",
            )

        if doc["status"] == DocumentStatus.CANCELLED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot credit a cancelled document")

        credit_number = await self._generate_document_number(company_id, DocumentType.CREDIT_NOTE)
        credit_doc = new_document(
            company_id=company_id,
            customer_id=doc["customer_id"],
            document_type=DocumentType.CREDIT_NOTE,
            document_number=credit_number,
            items=doc["items"],
            is_kleinunternehmer=doc.get("is_kleinunternehmer", False),
            notes=f"Gutschrift zu {doc['document_number']}",
            issue_date=datetime.utcnow().strftime("%Y-%m-%d"),
            due_date=datetime.utcnow().strftime("%Y-%m-%d"),
            related_document_id=document_id,
        )
        credit_id = await self.document_repo.insert_one(credit_doc)
        logger.info("Credit note %s created for document %s", credit_id, document_id)
        created = await self.document_repo.find_by_id(credit_id)
        return self._serialize_dates(created)

    # ------------------------------------------------------------------
    # RELATED DOCUMENTS
    # ------------------------------------------------------------------

    async def get_related_documents(
        self, company_id: str, document_id: str
    ) -> Dict[str, Any]:
        """Retrieve the parent document and all child documents linked to a document."""
        doc = await self.get_document(company_id, document_id)

        # Children: documents that reference this document
        children = await self.document_repo.find_related_documents(company_id, document_id)
        children_serialized = [
            {
                "id": c["id"],
                "document_number": c.get("document_number", ""),
                "document_type": c.get("document_type", ""),
                "status": c.get("status", ""),
                "gross": c.get("totals", {}).get("gross", 0),
            }
            for c in children
        ]

        # Parent: the document this one references
        parent = None
        related_id = doc.get("related_document_id", "")
        if related_id:
            try:
                parent_doc = await self.get_document(company_id, related_id)
                parent = {
                    "id": parent_doc["id"],
                    "document_number": parent_doc.get("document_number", ""),
                    "document_type": parent_doc.get("document_type", ""),
                    "status": parent_doc.get("status", ""),
                    "gross": parent_doc.get("totals", {}).get("gross", 0),
                }
            except HTTPException:
                pass

        return {"parent": parent, "children": children_serialized}

    # ------------------------------------------------------------------
    # PARTIAL INVOICES (Abschlagsrechnungen)
    # ------------------------------------------------------------------

    async def create_partial_invoice(
        self, company_id: str, document_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a PARTIAL_INVOICE linked to an existing invoice."""
        doc = await self.get_document(company_id, document_id)

        if doc["document_type"] != DocumentType.INVOICE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Partial invoices can only be created from invoices",
            )

        if doc["status"] == DocumentStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create partial invoice from a cancelled document",
            )

        # Check that sum of existing partial invoices + new amount does not exceed original gross
        existing_partials = await self.document_repo.find_related_documents(company_id, document_id)
        partial_sum = sum(
            abs(p.get("totals", {}).get("gross", 0))
            for p in existing_partials
            if p.get("document_type") == DocumentType.PARTIAL_INVOICE
        )
        original_gross = abs(doc.get("totals", {}).get("gross", 0))
        requested_amount = data["amount"]

        if partial_sum + requested_amount > original_gross + 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Partial total ({partial_sum + requested_amount:.2f}) would exceed invoice gross ({original_gross:.2f})",
            )

        company = await self.company_repo.find_by_id(company_id)
        is_kleinunternehmer = company.get("is_kleinunternehmer", False) if company else False

        # Resolve items: use provided items or create a single line item from the amount
        if data.get("items"):
            resolved_items = await self._resolve_line_items(company_id, data["items"], is_kleinunternehmer)
        else:
            vat_rate = 0.0 if is_kleinunternehmer else 0.19
            net_amount = round(requested_amount / (1 + vat_rate), 2) if vat_rate else requested_amount
            resolved_items = [new_line_item(
                product_id="",
                name=f"Abschlag zu {doc['document_number']}",
                description="",
                quantity=1,
                unit="Pauschal",
                unit_price=net_amount,
                vat_rate=vat_rate,
                discount_percent=0.0,
            )]

        partial_number = await self._generate_document_number(company_id, DocumentType.PARTIAL_INVOICE)
        issue_date = datetime.utcnow().strftime("%Y-%m-%d")
        payment_terms_days = data.get("payment_terms_days", 14)
        due_date = self._calc_due_date(issue_date, payment_terms_days)

        partial_doc = new_document(
            company_id=company_id,
            customer_id=doc["customer_id"],
            document_type=DocumentType.PARTIAL_INVOICE,
            document_number=partial_number,
            items=resolved_items,
            is_kleinunternehmer=is_kleinunternehmer,
            notes=data.get("notes", "") or f"Abschlagsrechnung zu {doc['document_number']}",
            payment_terms_days=payment_terms_days,
            issue_date=issue_date,
            due_date=due_date,
            related_document_id=document_id,
        )
        partial_id = await self.document_repo.insert_one(partial_doc)
        logger.info("Created partial invoice %s for document %s", partial_id, document_id)
        created = await self.document_repo.find_by_id(partial_id)
        return self._serialize_dates(created)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _resolve_line_items(
        self,
        company_id: str,
        items_data: List[Any],
        is_kleinunternehmer: bool,
    ) -> List[Dict[str, Any]]:
        """Resolve line items from product references, applying overrides and discounts.

        Items without a product_id are treated as free-text line items.
        """
        resolved: List[Dict[str, Any]] = []
        for item in items_data:
            item_dict = item if isinstance(item, dict) else item.dict()
            product_id = item_dict.get("product_id") or ""
            product = None

            if product_id:
                product = await self.product_repo.find_by_id(product_id)
                if not product or product.get("company_id") != company_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product {product_id} not found",
                    )

            if product:
                name = item_dict.get("name") or product["name"]
                description = item_dict.get("description") or product.get("description", "")
                unit = item_dict.get("unit") or product.get("unit", "Stück")
                unit_price = item_dict.get("unit_price") or product["unit_price"]
                vat_rate = item_dict.get("vat_rate") if item_dict.get("vat_rate") is not None else product.get("vat_rate", 0.19)
            else:
                name = item_dict.get("name") or item_dict.get("description") or "Position"
                description = item_dict.get("description") or ""
                unit = item_dict.get("unit") or "Stück"
                unit_price = item_dict.get("unit_price") or 0
                vat_rate = item_dict.get("vat_rate") if item_dict.get("vat_rate") is not None else 0.19

            discount_percent = item_dict.get("discount_percent", 0.0)

            if is_kleinunternehmer:
                vat_rate = 0.0

            line = new_line_item(
                product_id=product_id,
                name=name,
                description=description,
                quantity=item_dict["quantity"],
                unit=unit,
                unit_price=unit_price,
                vat_rate=vat_rate,
                discount_percent=discount_percent,
            )
            resolved.append(line)
        return resolved

    async def _generate_document_number(
        self, company_id: str, document_type: str
    ) -> str:
        """Generate the next sequential document number using atomic counter."""
        prefix = DOCUMENT_NUMBER_PREFIX.get(document_type, "DOC")
        counter_type = f"document_{document_type.lower()}"
        seq = await self.counter_repo.get_next_number(company_id, counter_type)
        return f"{prefix}-{seq:06d}"

    @staticmethod
    def _calc_due_date(issue_date: str, payment_terms_days: int) -> str:
        """Calculate the due date from issue date + payment terms."""
        dt = datetime.strptime(issue_date, "%Y-%m-%d") + timedelta(days=payment_terms_days)
        return dt.strftime("%Y-%m-%d")

    @staticmethod
    def _calc_totals(
        items: List[Dict[str, Any]],
        is_kleinunternehmer: bool,
        document_type: str,
    ) -> Dict[str, Any]:
        """Recalculate totals from resolved line items."""
        total_net = round(sum(i["net_amount"] for i in items), 2)
        total_vat = 0.0 if is_kleinunternehmer else round(sum(i["vat_amount"] for i in items), 2)
        total_gross = round(total_net + total_vat, 2)

        if document_type in (DocumentType.CREDIT_NOTE, DocumentType.CANCELLATION):
            total_net = -abs(total_net)
            total_vat = -abs(total_vat)
            total_gross = -abs(total_gross)

        return {
            "net": total_net,
            "vat": total_vat,
            "gross": total_gross,
            "paid_amount": 0.0,
            "remaining_amount": total_gross,
        }

    @staticmethod
    def _validate_status_transition(doc_type: str, current: str, target: str) -> None:
        """Ensure the status transition is valid for the document type."""
        _invoice_transitions = {
            DocumentStatus.DRAFT: [DocumentStatus.SENT, DocumentStatus.CANCELLED],
            DocumentStatus.SENT: [DocumentStatus.PAID, DocumentStatus.PARTIALLY_PAID, DocumentStatus.OVERDUE, DocumentStatus.CANCELLED],
            DocumentStatus.PARTIALLY_PAID: [DocumentStatus.PAID, DocumentStatus.OVERDUE, DocumentStatus.CANCELLED],
            DocumentStatus.OVERDUE: [DocumentStatus.PAID, DocumentStatus.PARTIALLY_PAID, DocumentStatus.CANCELLED],
        }
        allowed = {
            DocumentType.INVOICE: _invoice_transitions,
            DocumentType.PARTIAL_INVOICE: _invoice_transitions,
            DocumentType.QUOTE: {
                DocumentStatus.DRAFT: [DocumentStatus.SENT, DocumentStatus.CANCELLED],
                DocumentStatus.SENT: [DocumentStatus.ACCEPTED, DocumentStatus.REJECTED, DocumentStatus.CANCELLED],
                DocumentStatus.ACCEPTED: [DocumentStatus.CONVERTED],
            },
            DocumentType.DELIVERY_NOTE: {
                DocumentStatus.DRAFT: [DocumentStatus.SENT, DocumentStatus.CANCELLED],
            },
            DocumentType.ORDER_CONFIRMATION: {
                DocumentStatus.DRAFT: [DocumentStatus.SENT, DocumentStatus.CANCELLED],
            },
            DocumentType.CREDIT_NOTE: {
                DocumentStatus.DRAFT: [DocumentStatus.SENT, DocumentStatus.CANCELLED],
            },
            DocumentType.CANCELLATION: {
                DocumentStatus.DRAFT: [DocumentStatus.SENT],
            },
        }
        transitions = allowed.get(doc_type, {})
        valid_targets = transitions.get(current, [])
        if target not in valid_targets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from {current} to {target} for {doc_type}",
            )

    @staticmethod
    def _serialize_dates(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert datetime objects to ISO strings for JSON serialization."""
        for field in ("created_at", "updated_at"):
            val = doc.get(field)
            if isinstance(val, datetime):
                doc[field] = val.isoformat()
        return doc
