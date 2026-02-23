const XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>'

function escapeXml(value) {
  return String(value || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;')
}

function amount(value) {
  return Number(value || 0).toFixed(2)
}

function dateCompact(value) {
  if (!value) return ''
  return String(value).replaceAll('-', '')
}

function groupedVat(document) {
  const map = new Map()
  for (const item of document.items || []) {
    const rate = Number(item.vat_rate || 0)
    if (!map.has(rate)) {
      map.set(rate, { rate, net: 0, vat: 0 })
    }
    const entry = map.get(rate)
    entry.net += Number(item.net_amount || 0)
    entry.vat += Number(item.vat_amount || 0)
  }
  return Array.from(map.values()).sort((a, b) => b.rate - a.rate)
}

export function buildXRechnungXml(document, company, customer) {
  const vatRows = groupedVat(document)
    .map(
      (vat) => `
      <cac:TaxSubtotal>
        <cbc:TaxableAmount currencyID="EUR">${amount(vat.net)}</cbc:TaxableAmount>
        <cbc:TaxAmount currencyID="EUR">${amount(vat.vat)}</cbc:TaxAmount>
        <cac:TaxCategory>
          <cbc:ID>${vat.rate > 0 ? 'S' : 'Z'}</cbc:ID>
          <cbc:Percent>${(vat.rate * 100).toFixed(2)}</cbc:Percent>
          <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
        </cac:TaxCategory>
      </cac:TaxSubtotal>`
    )
    .join('\n')

  const invoiceLines = (document.items || [])
    .map(
      (item, index) => `
      <cac:InvoiceLine>
        <cbc:ID>${index + 1}</cbc:ID>
        <cbc:InvoicedQuantity unitCode="C62">${Number(item.quantity || 0).toFixed(2)}</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="EUR">${amount(item.net_amount)}</cbc:LineExtensionAmount>
        <cac:Item><cbc:Name>${escapeXml(item.name || item.description || '-')}</cbc:Name></cac:Item>
        <cac:Price><cbc:PriceAmount currencyID="EUR">${amount(item.unit_price)}</cbc:PriceAmount></cac:Price>
      </cac:InvoiceLine>`
    )
    .join('\n')

  return `${XML_HEADER}
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:xoev-de:kosit:standard:xrechnung_2.0</cbc:CustomizationID>
  <cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>
  <cbc:ID>${escapeXml(document.document_number)}</cbc:ID>
  <cbc:IssueDate>${escapeXml(document.issue_date)}</cbc:IssueDate>
  <cbc:DueDate>${escapeXml(document.due_date)}</cbc:DueDate>
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
  <cac:AccountingSupplierParty><cac:Party><cac:PartyName><cbc:Name>${escapeXml(company?.name)}</cbc:Name></cac:PartyName></cac:Party></cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty><cac:Party><cac:PartyName><cbc:Name>${escapeXml(customer?.name || document.customer_name)}</cbc:Name></cac:PartyName></cac:Party></cac:AccountingCustomerParty>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="EUR">${amount(document.totals?.vat)}</cbc:TaxAmount>
${vatRows}
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="EUR">${amount(document.totals?.net)}</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="EUR">${amount(document.totals?.net)}</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="EUR">${amount(document.totals?.gross)}</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="EUR">${amount(document.totals?.gross)}</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
${invoiceLines}
</Invoice>`
}

export function buildZugferdXml(document, company, customer) {
  return `${XML_HEADER}
<rsm:CrossIndustryInvoice
  xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
  xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
  xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocumentContext>
    <ram:GuidelineSpecifiedDocumentContextParameter>
      <ram:ID>urn:cen.eu:en16931:2017#conformant#urn:factur-x.eu:1p0:comfort</ram:ID>
    </ram:GuidelineSpecifiedDocumentContextParameter>
  </rsm:ExchangedDocumentContext>
  <rsm:ExchangedDocument>
    <ram:ID>${escapeXml(document.document_number)}</ram:ID>
    <ram:TypeCode>380</ram:TypeCode>
    <ram:IssueDateTime><udt:DateTimeString format="102">${dateCompact(document.issue_date)}</udt:DateTimeString></ram:IssueDateTime>
  </rsm:ExchangedDocument>
  <rsm:SupplyChainTradeTransaction>
    <ram:ApplicableHeaderTradeAgreement>
      <ram:SellerTradeParty><ram:Name>${escapeXml(company?.name)}</ram:Name></ram:SellerTradeParty>
      <ram:BuyerTradeParty><ram:Name>${escapeXml(customer?.name || document.customer_name)}</ram:Name></ram:BuyerTradeParty>
    </ram:ApplicableHeaderTradeAgreement>
    <ram:ApplicableHeaderTradeSettlement>
      <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
      <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        <ram:LineTotalAmount>${amount(document.totals?.net)}</ram:LineTotalAmount>
        <ram:TaxBasisTotalAmount>${amount(document.totals?.net)}</ram:TaxBasisTotalAmount>
        <ram:TaxTotalAmount currencyID="EUR">${amount(document.totals?.vat)}</ram:TaxTotalAmount>
        <ram:GrandTotalAmount>${amount(document.totals?.gross)}</ram:GrandTotalAmount>
        <ram:DuePayableAmount>${amount(document.totals?.gross)}</ram:DuePayableAmount>
      </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
    </ram:ApplicableHeaderTradeSettlement>
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>`
}

export function downloadXml(filename, xmlString) {
  const blob = new Blob([xmlString], { type: 'application/xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}
