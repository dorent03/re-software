"""E-invoice XML generation service — XRechnung and ZUGFeRD."""

import logging
from datetime import datetime
from typing import Any, Dict
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from fastapi import HTTPException, status

from app.core.config import settings
from app.repositories.company_repository import CompanyRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.document_repository import DocumentRepository

logger = logging.getLogger(__name__)

# UBL / CII namespaces
NS_UBL_INVOICE = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"

NS_CII_RSM = "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
NS_CII_RAM = "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
NS_CII_QDT = "urn:un:unece:uncefact:data:standard:QualifiedDataType:100"
NS_CII_UDT = "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100"


class EInvoiceService:
    """Generates XRechnung (UBL) and ZUGFeRD (CII) XML."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        company_repo: CompanyRepository,
        customer_repo: CustomerRepository,
    ):
        self.document_repo = document_repo
        self.company_repo = company_repo
        self.customer_repo = customer_repo

    async def generate_xrechnung(
        self, company_id: str, document_id: str
    ) -> str:
        """Generate XRechnung (UBL 2.1) XML for an invoice."""
        doc, company, customer = await self._load_context(company_id, document_id)
        xml_str = self._build_ubl_xml(doc, company, customer)
        logger.info("Generated XRechnung XML for document %s", document_id)
        return xml_str

    async def generate_zugferd(
        self, company_id: str, document_id: str
    ) -> str:
        """Generate ZUGFeRD (Cross-Industry Invoice) XML for an invoice."""
        doc, company, customer = await self._load_context(company_id, document_id)
        xml_str = self._build_cii_xml(doc, company, customer)
        logger.info("Generated ZUGFeRD XML for document %s", document_id)
        return xml_str

    async def _load_context(
        self, company_id: str, document_id: str
    ):
        """Load and validate the document, company, and customer."""
        doc = await self.document_repo.find_by_id(document_id)
        if not doc or doc.get("company_id") != company_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        if doc["document_type"] not in ("INVOICE", "PARTIAL_INVOICE", "CREDIT_NOTE", "CANCELLATION"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-invoicing only supported for invoices, credit notes, and cancellations",
            )

        company = await self.company_repo.find_by_id(company_id)
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

        customer = await self.customer_repo.find_by_id(doc["customer_id"])
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

        return doc, company, customer

    # ------------------------------------------------------------------
    # XRechnung (UBL 2.1)
    # ------------------------------------------------------------------

    def _build_ubl_xml(
        self, doc: Dict[str, Any], company: Dict[str, Any], customer: Dict[str, Any]
    ) -> str:
        """Build a simplified UBL 2.1 Invoice XML conforming to XRechnung."""
        root = Element("Invoice")
        root.set("xmlns", NS_UBL_INVOICE)
        root.set("xmlns:cac", NS_CAC)
        root.set("xmlns:cbc", NS_CBC)

        # Customization and profile
        SubElement(root, f"{{{NS_CBC}}}CustomizationID").text = (
            "urn:cen.eu:en16931:2017#compliant#urn:xoev-de:kosit:standard:xrechnung_2.0"
        )
        SubElement(root, f"{{{NS_CBC}}}ProfileID").text = (
            "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"
        )

        SubElement(root, f"{{{NS_CBC}}}ID").text = doc["document_number"]
        SubElement(root, f"{{{NS_CBC}}}IssueDate").text = doc.get("issue_date", "")
        SubElement(root, f"{{{NS_CBC}}}DueDate").text = doc.get("due_date", "")
        SubElement(root, f"{{{NS_CBC}}}InvoiceTypeCode").text = "380"
        SubElement(root, f"{{{NS_CBC}}}DocumentCurrencyCode").text = "EUR"

        # Supplier
        supplier_party = SubElement(root, f"{{{NS_CAC}}}AccountingSupplierParty")
        sp = SubElement(supplier_party, f"{{{NS_CAC}}}Party")
        sp_name = SubElement(sp, f"{{{NS_CAC}}}PartyName")
        SubElement(sp_name, f"{{{NS_CBC}}}Name").text = company.get("name", "")
        sp_addr = SubElement(sp, f"{{{NS_CAC}}}PostalAddress")
        SubElement(sp_addr, f"{{{NS_CBC}}}StreetName").text = company.get("street", "")
        SubElement(sp_addr, f"{{{NS_CBC}}}CityName").text = company.get("city", "")
        SubElement(sp_addr, f"{{{NS_CBC}}}PostalZone").text = company.get("zip_code", "")
        sp_country = SubElement(sp_addr, f"{{{NS_CAC}}}Country")
        SubElement(sp_country, f"{{{NS_CBC}}}IdentificationCode").text = company.get("country", "DE")
        if company.get("tax_id"):
            sp_tax = SubElement(sp, f"{{{NS_CAC}}}PartyTaxScheme")
            SubElement(sp_tax, f"{{{NS_CBC}}}CompanyID").text = company["tax_id"]
            sp_ts = SubElement(sp_tax, f"{{{NS_CAC}}}TaxScheme")
            SubElement(sp_ts, f"{{{NS_CBC}}}ID").text = "VAT"

        # Customer
        cust_party = SubElement(root, f"{{{NS_CAC}}}AccountingCustomerParty")
        cp = SubElement(cust_party, f"{{{NS_CAC}}}Party")
        cp_name = SubElement(cp, f"{{{NS_CAC}}}PartyName")
        SubElement(cp_name, f"{{{NS_CBC}}}Name").text = customer.get("name", "")
        cp_addr = SubElement(cp, f"{{{NS_CAC}}}PostalAddress")
        SubElement(cp_addr, f"{{{NS_CBC}}}StreetName").text = customer.get("street", "")
        SubElement(cp_addr, f"{{{NS_CBC}}}CityName").text = customer.get("city", "")
        SubElement(cp_addr, f"{{{NS_CBC}}}PostalZone").text = customer.get("zip_code", "")
        cp_country = SubElement(cp_addr, f"{{{NS_CAC}}}Country")
        SubElement(cp_country, f"{{{NS_CBC}}}IdentificationCode").text = customer.get("country", "DE")

        # Payment means
        pay_means = SubElement(root, f"{{{NS_CAC}}}PaymentMeans")
        SubElement(pay_means, f"{{{NS_CBC}}}PaymentMeansCode").text = "58"
        if company.get("iban"):
            pay_acct = SubElement(pay_means, f"{{{NS_CAC}}}PayeeFinancialAccount")
            SubElement(pay_acct, f"{{{NS_CBC}}}ID").text = company["iban"]
            if company.get("bic"):
                fin_inst = SubElement(pay_acct, f"{{{NS_CAC}}}FinancialInstitutionBranch")
                SubElement(fin_inst, f"{{{NS_CBC}}}ID").text = company["bic"]

        # Tax total
        totals = doc.get("totals", {})
        tax_total_el = SubElement(root, f"{{{NS_CAC}}}TaxTotal")
        tax_amount_el = SubElement(tax_total_el, f"{{{NS_CBC}}}TaxAmount")
        tax_amount_el.set("currencyID", "EUR")
        tax_amount_el.text = f"{abs(totals.get('vat', 0)):.2f}"

        # Build VAT subtotals per rate
        vat_groups: Dict[float, float] = {}
        vat_net_groups: Dict[float, float] = {}
        for item in doc.get("items", []):
            rate = item.get("vat_rate", 0)
            vat_groups[rate] = vat_groups.get(rate, 0) + abs(item.get("vat_amount", 0))
            vat_net_groups[rate] = vat_net_groups.get(rate, 0) + abs(item.get("net_amount", 0))

        for rate, vat_amt in vat_groups.items():
            subtotal = SubElement(tax_total_el, f"{{{NS_CAC}}}TaxSubtotal")
            taxable_el = SubElement(subtotal, f"{{{NS_CBC}}}TaxableAmount")
            taxable_el.set("currencyID", "EUR")
            taxable_el.text = f"{vat_net_groups.get(rate, 0):.2f}"
            sub_tax_el = SubElement(subtotal, f"{{{NS_CBC}}}TaxAmount")
            sub_tax_el.set("currencyID", "EUR")
            sub_tax_el.text = f"{vat_amt:.2f}"
            tax_cat = SubElement(subtotal, f"{{{NS_CAC}}}TaxCategory")
            SubElement(tax_cat, f"{{{NS_CBC}}}ID").text = "S" if rate > 0 else "Z"
            SubElement(tax_cat, f"{{{NS_CBC}}}Percent").text = f"{rate * 100:.0f}"
            ts = SubElement(tax_cat, f"{{{NS_CAC}}}TaxScheme")
            SubElement(ts, f"{{{NS_CBC}}}ID").text = "VAT"

        # Legal monetary total
        monetary = SubElement(root, f"{{{NS_CAC}}}LegalMonetaryTotal")
        net_el = SubElement(monetary, f"{{{NS_CBC}}}LineExtensionAmount")
        net_el.set("currencyID", "EUR")
        net_el.text = f"{abs(totals.get('net', 0)):.2f}"
        excl_el = SubElement(monetary, f"{{{NS_CBC}}}TaxExclusiveAmount")
        excl_el.set("currencyID", "EUR")
        excl_el.text = f"{abs(totals.get('net', 0)):.2f}"
        incl_el = SubElement(monetary, f"{{{NS_CBC}}}TaxInclusiveAmount")
        incl_el.set("currencyID", "EUR")
        incl_el.text = f"{abs(totals.get('gross', 0)):.2f}"
        payable_el = SubElement(monetary, f"{{{NS_CBC}}}PayableAmount")
        payable_el.set("currencyID", "EUR")
        payable_el.text = f"{abs(totals.get('remaining_amount', totals.get('gross', 0))):.2f}"

        # Invoice lines
        for idx, item in enumerate(doc.get("items", []), start=1):
            line = SubElement(root, f"{{{NS_CAC}}}InvoiceLine")
            SubElement(line, f"{{{NS_CBC}}}ID").text = str(idx)
            qty_el = SubElement(line, f"{{{NS_CBC}}}InvoicedQuantity")
            qty_el.set("unitCode", "C62")
            qty_el.text = f"{item['quantity']:.2f}"
            line_ext = SubElement(line, f"{{{NS_CBC}}}LineExtensionAmount")
            line_ext.set("currencyID", "EUR")
            line_ext.text = f"{abs(item.get('net_amount', 0)):.2f}"

            li_item = SubElement(line, f"{{{NS_CAC}}}Item")
            SubElement(li_item, f"{{{NS_CBC}}}Name").text = item.get("name", "")
            if item.get("description"):
                SubElement(li_item, f"{{{NS_CBC}}}Description").text = item["description"]
            li_tax = SubElement(li_item, f"{{{NS_CAC}}}ClassifiedTaxCategory")
            SubElement(li_tax, f"{{{NS_CBC}}}ID").text = "S" if item.get("vat_rate", 0) > 0 else "Z"
            SubElement(li_tax, f"{{{NS_CBC}}}Percent").text = f"{item.get('vat_rate', 0) * 100:.0f}"
            li_ts = SubElement(li_tax, f"{{{NS_CAC}}}TaxScheme")
            SubElement(li_ts, f"{{{NS_CBC}}}ID").text = "VAT"

            li_price = SubElement(line, f"{{{NS_CAC}}}Price")
            price_el = SubElement(li_price, f"{{{NS_CBC}}}PriceAmount")
            price_el.set("currencyID", "EUR")
            price_el.text = f"{item.get('unit_price', 0):.2f}"

        return self._prettify(root)

    # ------------------------------------------------------------------
    # ZUGFeRD (CII - Cross-Industry Invoice)
    # ------------------------------------------------------------------

    def _build_cii_xml(
        self, doc: Dict[str, Any], company: Dict[str, Any], customer: Dict[str, Any]
    ) -> str:
        """Build a ZUGFeRD Comfort profile CII XML."""
        root = Element(f"{{{NS_CII_RSM}}}CrossIndustryInvoice")
        root.set("xmlns:rsm", NS_CII_RSM)
        root.set("xmlns:ram", NS_CII_RAM)
        root.set("xmlns:qdt", NS_CII_QDT)
        root.set("xmlns:udt", NS_CII_UDT)

        # Exchange context
        ctx = SubElement(root, f"{{{NS_CII_RSM}}}ExchangedDocumentContext")
        guideline = SubElement(ctx, f"{{{NS_CII_RAM}}}GuidelineSpecifiedDocumentContextParameter")
        SubElement(guideline, f"{{{NS_CII_RAM}}}ID").text = (
            "urn:cen.eu:en16931:2017#conformant#urn:factur-x.eu:1p0:comfort"
        )

        # Exchanged document
        ex_doc = SubElement(root, f"{{{NS_CII_RSM}}}ExchangedDocument")
        SubElement(ex_doc, f"{{{NS_CII_RAM}}}ID").text = doc["document_number"]
        SubElement(ex_doc, f"{{{NS_CII_RAM}}}TypeCode").text = "380"
        issue_dt = SubElement(ex_doc, f"{{{NS_CII_RAM}}}IssueDateTime")
        dt_str = SubElement(issue_dt, f"{{{NS_CII_UDT}}}DateTimeString")
        dt_str.set("format", "102")
        dt_str.text = doc.get("issue_date", "").replace("-", "")

        # Supply chain trade transaction
        transaction = SubElement(root, f"{{{NS_CII_RSM}}}SupplyChainTradeTransaction")

        # Line items
        for idx, item in enumerate(doc.get("items", []), start=1):
            line = SubElement(transaction, f"{{{NS_CII_RAM}}}IncludedSupplyChainTradeLineItem")
            line_doc = SubElement(line, f"{{{NS_CII_RAM}}}AssociatedDocumentLineDocument")
            SubElement(line_doc, f"{{{NS_CII_RAM}}}LineID").text = str(idx)

            trade_product = SubElement(line, f"{{{NS_CII_RAM}}}SpecifiedTradeProduct")
            SubElement(trade_product, f"{{{NS_CII_RAM}}}Name").text = item.get("name", "")

            line_agreement = SubElement(line, f"{{{NS_CII_RAM}}}SpecifiedLineTradeAgreement")
            net_price = SubElement(line_agreement, f"{{{NS_CII_RAM}}}NetPriceProductTradePrice")
            SubElement(net_price, f"{{{NS_CII_RAM}}}ChargeAmount").text = f"{item.get('unit_price', 0):.2f}"

            line_delivery = SubElement(line, f"{{{NS_CII_RAM}}}SpecifiedLineTradeDelivery")
            SubElement(line_delivery, f"{{{NS_CII_RAM}}}BilledQuantity").text = f"{item.get('quantity', 0):.2f}"

            line_settlement = SubElement(line, f"{{{NS_CII_RAM}}}SpecifiedLineTradeSettlement")
            line_tax = SubElement(line_settlement, f"{{{NS_CII_RAM}}}ApplicableTradeTax")
            SubElement(line_tax, f"{{{NS_CII_RAM}}}TypeCode").text = "VAT"
            SubElement(line_tax, f"{{{NS_CII_RAM}}}CategoryCode").text = "S" if item.get("vat_rate", 0) > 0 else "Z"
            SubElement(line_tax, f"{{{NS_CII_RAM}}}RateApplicablePercent").text = f"{item.get('vat_rate', 0) * 100:.0f}"

            line_sum = SubElement(line_settlement, f"{{{NS_CII_RAM}}}SpecifiedTradeSettlementLineMonetarySummation")
            SubElement(line_sum, f"{{{NS_CII_RAM}}}LineTotalAmount").text = f"{abs(item.get('net_amount', 0)):.2f}"

        # Header trade agreement
        agreement = SubElement(transaction, f"{{{NS_CII_RAM}}}ApplicableHeaderTradeAgreement")
        # Seller
        seller = SubElement(agreement, f"{{{NS_CII_RAM}}}SellerTradeParty")
        SubElement(seller, f"{{{NS_CII_RAM}}}Name").text = company.get("name", "")
        seller_addr = SubElement(seller, f"{{{NS_CII_RAM}}}PostalTradeAddress")
        SubElement(seller_addr, f"{{{NS_CII_RAM}}}LineOne").text = company.get("street", "")
        SubElement(seller_addr, f"{{{NS_CII_RAM}}}PostcodeCode").text = company.get("zip_code", "")
        SubElement(seller_addr, f"{{{NS_CII_RAM}}}CityName").text = company.get("city", "")
        SubElement(seller_addr, f"{{{NS_CII_RAM}}}CountryID").text = company.get("country", "DE")
        if company.get("tax_id"):
            seller_tax = SubElement(seller, f"{{{NS_CII_RAM}}}SpecifiedTaxRegistration")
            tax_id_el = SubElement(seller_tax, f"{{{NS_CII_RAM}}}ID")
            tax_id_el.set("schemeID", "VA")
            tax_id_el.text = company["tax_id"]

        # Buyer
        buyer = SubElement(agreement, f"{{{NS_CII_RAM}}}BuyerTradeParty")
        SubElement(buyer, f"{{{NS_CII_RAM}}}Name").text = customer.get("name", "")
        buyer_addr = SubElement(buyer, f"{{{NS_CII_RAM}}}PostalTradeAddress")
        SubElement(buyer_addr, f"{{{NS_CII_RAM}}}LineOne").text = customer.get("street", "")
        SubElement(buyer_addr, f"{{{NS_CII_RAM}}}PostcodeCode").text = customer.get("zip_code", "")
        SubElement(buyer_addr, f"{{{NS_CII_RAM}}}CityName").text = customer.get("city", "")
        SubElement(buyer_addr, f"{{{NS_CII_RAM}}}CountryID").text = customer.get("country", "DE")

        # Header trade delivery
        SubElement(transaction, f"{{{NS_CII_RAM}}}ApplicableHeaderTradeDelivery")

        # Header trade settlement
        settlement = SubElement(transaction, f"{{{NS_CII_RAM}}}ApplicableHeaderTradeSettlement")
        SubElement(settlement, f"{{{NS_CII_RAM}}}InvoiceCurrencyCode").text = "EUR"

        # Payment means
        if company.get("iban"):
            pay_means = SubElement(settlement, f"{{{NS_CII_RAM}}}SpecifiedTradeSettlementPaymentMeans")
            SubElement(pay_means, f"{{{NS_CII_RAM}}}TypeCode").text = "58"
            payee_acct = SubElement(pay_means, f"{{{NS_CII_RAM}}}PayeePartyDebtorFinancialAccount")
            SubElement(payee_acct, f"{{{NS_CII_RAM}}}IBANID").text = company["iban"]

        # Tax
        totals = doc.get("totals", {})
        tax = SubElement(settlement, f"{{{NS_CII_RAM}}}ApplicableTradeTax")
        SubElement(tax, f"{{{NS_CII_RAM}}}CalculatedAmount").text = f"{abs(totals.get('vat', 0)):.2f}"
        SubElement(tax, f"{{{NS_CII_RAM}}}TypeCode").text = "VAT"
        SubElement(tax, f"{{{NS_CII_RAM}}}BasisAmount").text = f"{abs(totals.get('net', 0)):.2f}"
        SubElement(tax, f"{{{NS_CII_RAM}}}CategoryCode").text = "S"

        # Monetary summation
        summary = SubElement(settlement, f"{{{NS_CII_RAM}}}SpecifiedTradeSettlementHeaderMonetarySummation")
        SubElement(summary, f"{{{NS_CII_RAM}}}LineTotalAmount").text = f"{abs(totals.get('net', 0)):.2f}"
        SubElement(summary, f"{{{NS_CII_RAM}}}TaxBasisTotalAmount").text = f"{abs(totals.get('net', 0)):.2f}"
        tax_total_el = SubElement(summary, f"{{{NS_CII_RAM}}}TaxTotalAmount")
        tax_total_el.set("currencyID", "EUR")
        tax_total_el.text = f"{abs(totals.get('vat', 0)):.2f}"
        SubElement(summary, f"{{{NS_CII_RAM}}}GrandTotalAmount").text = f"{abs(totals.get('gross', 0)):.2f}"
        SubElement(summary, f"{{{NS_CII_RAM}}}DuePayableAmount").text = (
            f"{abs(totals.get('remaining_amount', totals.get('gross', 0))):.2f}"
        )

        return self._prettify(root)

    @staticmethod
    def _prettify(element: Element) -> str:
        """Return a pretty-printed XML string."""
        rough = tostring(element, encoding="unicode", xml_declaration=True)
        parsed = minidom.parseString(rough)
        return parsed.toprettyxml(indent="  ", encoding=None)
