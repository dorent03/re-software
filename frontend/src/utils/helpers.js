/**
 * Format a number as EUR currency string.
 * @param {number} value
 * @returns {string}
 */
export function formatCurrency(value) {
  if (value == null) return '0,00 €'
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
  }).format(value)
}

/**
 * Format an ISO date string to German locale.
 * @param {string} dateStr – YYYY-MM-DD or ISO string
 * @returns {string}
 */
export function formatDate(dateStr) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

/**
 * Return a Tailwind badge class based on document status.
 * @param {string} status
 * @returns {string}
 */
export function statusBadgeClass(status) {
  const map = {
    DRAFT: 'badge-gray',
    SENT: 'badge-blue',
    PAID: 'badge-green',
    PARTIALLY_PAID: 'badge-yellow',
    OVERDUE: 'badge-red',
    CANCELLED: 'badge-red',
    ACCEPTED: 'badge-green',
    REJECTED: 'badge-red',
    CONVERTED: 'badge-blue',
  }
  return map[status] || 'badge-gray'
}

/**
 * Map document type to German label.
 * @param {string} type
 * @returns {string}
 */
export function documentTypeLabel(type) {
  const map = {
    INVOICE: 'Rechnung',
    QUOTE: 'Angebot',
    DELIVERY_NOTE: 'Lieferschein',
    ORDER_CONFIRMATION: 'Auftragsbestätigung',
    PARTIAL_INVOICE: 'Abschlagsrechnung',
    CREDIT_NOTE: 'Gutschrift',
    CANCELLATION: 'Stornorechnung',
  }
  return map[type] || type
}

/**
 * Calculate line item totals with discount.
 * @param {{ quantity: number, unit_price: number, discount_percent: number, vat_rate: number }} item
 * @returns {{ net_amount: number, vat_amount: number, gross_amount: number, discount_amount: number }}
 */
export function calcLineItem(item) {
  const subtotal = +(item.quantity * item.unit_price).toFixed(2)
  const discountAmount = +((subtotal * (item.discount_percent || 0)) / 100).toFixed(2)
  const netAmount = +(subtotal - discountAmount).toFixed(2)
  const vatAmount = +(netAmount * (item.vat_rate || 0)).toFixed(2)
  const grossAmount = +(netAmount + vatAmount).toFixed(2)
  return { net_amount: netAmount, vat_amount: vatAmount, gross_amount: grossAmount, discount_amount: discountAmount }
}

/**
 * Sum document totals from line items.
 * @param {Array} items
 * @param {boolean} isKleinunternehmer
 * @returns {{ net: number, vat: number, gross: number }}
 */
export function calcDocumentTotals(items, isKleinunternehmer = false) {
  let net = 0
  let vat = 0
  for (const item of items) {
    const calc = calcLineItem(item)
    net += calc.net_amount
    vat += isKleinunternehmer ? 0 : calc.vat_amount
  }
  net = +net.toFixed(2)
  vat = +vat.toFixed(2)
  return { net, vat, gross: +(net + vat).toFixed(2) }
}
