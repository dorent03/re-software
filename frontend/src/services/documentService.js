import { db, nowIso, toDateOnly, normalizeId } from '@/db'
import { calcLineItem, calcDocumentTotals } from '@/utils/helpers'

const DOCUMENT_PREFIX = {
  INVOICE: 'INV',
  QUOTE: 'QUO',
  DELIVERY_NOTE: 'LS',
  ORDER_CONFIRMATION: 'AB',
  PARTIAL_INVOICE: 'TINV',
  CREDIT_NOTE: 'GS',
  CANCELLATION: 'ST',
}

const MAX_REMINDER_LEVEL = 3
const MONEY_EPSILON = 0.01

const ALLOWED_STATUS = {
  INVOICE: {
    DRAFT: ['SENT', 'CANCELLED'],
    SENT: ['PAID', 'PARTIALLY_PAID', 'OVERDUE', 'CANCELLED'],
    PARTIALLY_PAID: ['PAID', 'OVERDUE', 'CANCELLED'],
    OVERDUE: ['PAID', 'PARTIALLY_PAID', 'CANCELLED'],
    PAID: [],
    CANCELLED: [],
  },
  PARTIAL_INVOICE: {
    DRAFT: ['SENT', 'CANCELLED'],
    SENT: ['PAID', 'PARTIALLY_PAID', 'OVERDUE', 'CANCELLED'],
    PARTIALLY_PAID: ['PAID', 'OVERDUE', 'CANCELLED'],
    OVERDUE: ['PAID', 'PARTIALLY_PAID', 'CANCELLED'],
    PAID: [],
    CANCELLED: [],
  },
  QUOTE: {
    DRAFT: ['SENT', 'CANCELLED'],
    SENT: ['ACCEPTED', 'REJECTED', 'CANCELLED'],
    ACCEPTED: ['CONVERTED'],
    REJECTED: [],
    CONVERTED: [],
    CANCELLED: [],
  },
}

function addDaysToDateOnly(baseDate, days) {
  const date = new Date(baseDate)
  date.setDate(date.getDate() + Number(days || 0))
  return toDateOnly(date)
}

function asNumber(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function assertStatusTransition(documentType, fromStatus, toStatus) {
  const byType = ALLOWED_STATUS[documentType]
  if (!byType) return
  const allowedTargets = byType[fromStatus] || []
  if (!allowedTargets.includes(toStatus)) {
    throw new Error(`Ungültiger Statuswechsel: ${fromStatus} -> ${toStatus}`)
  }
}

async function getCompanySnapshot() {
  const company = await db.company.orderBy('id').last()
  if (!company) {
    return { company_name: '', company_iban: '', company_bic: '', is_kleinunternehmer: false }
  }
  return {
    company_name: company.name || '',
    company_iban: company.iban || '',
    company_bic: company.bic || '',
    is_kleinunternehmer: !!company.kleinunternehmer,
  }
}

async function buildLineItems(items, isKleinunternehmer) {
  const resolved = []
  for (const item of items) {
    const productId = item.product_id ? normalizeId(item.product_id) : ''
    let product = null
    if (productId) {
      product = await db.products.get(Number(productId))
    }
    const vatRate = isKleinunternehmer ? 0 : asNumber(item.vat_rate ?? product?.vat_rate, 0.19)
    const quantity = asNumber(item.quantity, 0)
    const unitPrice = asNumber(item.unit_price ?? product?.unit_price, 0)
    const discountPercent = asNumber(item.discount_percent, 0)
    const computed = calcLineItem({ quantity, unit_price: unitPrice, discount_percent: discountPercent, vat_rate: vatRate })

    resolved.push({
      product_id: productId || null,
      name: item.name || product?.name || '',
      description: item.description || product?.description || '',
      quantity,
      unit: item.unit || product?.unit || 'Stück',
      unit_price: unitPrice,
      vat_rate: vatRate,
      discount_percent: discountPercent,
      discount_amount: computed.discount_amount,
      net_amount: computed.net_amount,
      vat_amount: isKleinunternehmer ? 0 : computed.vat_amount,
      gross_amount: isKleinunternehmer ? computed.net_amount : computed.gross_amount,
    })
  }
  return resolved
}

async function nextDocumentNumber(documentType) {
  const key = `document:${documentType}`
  const existing = await db.counters.where('key').equals(key).first()
  if (!existing) {
    await db.counters.add({ key, value: 1, updated_at: nowIso() })
    return `${DOCUMENT_PREFIX[documentType] || 'DOC'}-000001`
  }
  const nextValue = Number(existing.value) + 1
  await db.counters.update(existing.id, { value: nextValue, updated_at: nowIso() })
  return `${DOCUMENT_PREFIX[documentType] || 'DOC'}-${String(nextValue).padStart(6, '0')}`
}

function normalizeTotals(totals, type) {
  if (!['CREDIT_NOTE', 'CANCELLATION'].includes(type)) return totals
  return {
    net: -Math.abs(totals.net),
    vat: -Math.abs(totals.vat),
    gross: -Math.abs(totals.gross),
    paid_amount: 0,
    remaining_amount: -Math.abs(totals.gross),
  }
}

export async function createDocument(payload) {
  const company = await getCompanySnapshot()
  const customer = await db.customers.get(Number(payload.customer_id))
  if (!customer) throw new Error('Kunde nicht gefunden')
  const issueDate = payload.issue_date || toDateOnly()
  const dueDate = addDaysToDateOnly(issueDate, payload.payment_terms_days ?? 14)
  const items = await buildLineItems(payload.items || [], company.is_kleinunternehmer)
  const calculated = calcDocumentTotals(items, company.is_kleinunternehmer)
  const totals = normalizeTotals({ ...calculated, paid_amount: 0, remaining_amount: calculated.gross }, payload.document_type)

  const document = {
    document_number: await nextDocumentNumber(payload.document_type),
    document_type: payload.document_type,
    status: 'DRAFT',
    customer_id: normalizeId(payload.customer_id),
    customer_name: customer.name || '',
    items,
    notes: payload.notes || '',
    payment_terms_days: Number(payload.payment_terms_days ?? 14),
    issue_date: issueDate,
    service_date: payload.service_date || '',
    due_date: dueDate,
    related_document_id: payload.related_document_id ? normalizeId(payload.related_document_id) : '',
    totals,
    payments: [],
    reminders: [],
    company_name: company.company_name,
    company_iban: company.company_iban,
    company_bic: company.company_bic,
    is_kleinunternehmer: company.is_kleinunternehmer,
    total_gross: totals.gross,
    created_at: nowIso(),
    updated_at: nowIso(),
  }

  const id = await db.documents.add(document)
  return { id: String(id), ...document }
}

export async function updateDocument(id, payload) {
  const existing = await db.documents.get(Number(id))
  if (!existing) throw new Error('Dokument nicht gefunden')
  if (existing.status !== 'DRAFT') throw new Error('Nur Entwürfe können bearbeitet werden')

  const company = await getCompanySnapshot()
  const customer = await db.customers.get(Number(payload.customer_id || existing.customer_id))
  if (!customer) throw new Error('Kunde nicht gefunden')

  const issueDate = existing.issue_date || toDateOnly()
  const paymentTerms = Number(payload.payment_terms_days ?? existing.payment_terms_days ?? 14)
  const dueDate = addDaysToDateOnly(issueDate, paymentTerms)
  const items = await buildLineItems(payload.items || existing.items || [], company.is_kleinunternehmer)
  const calculated = calcDocumentTotals(items, company.is_kleinunternehmer)

  const nextData = {
    ...existing,
    document_type: payload.document_type || existing.document_type,
    customer_id: normalizeId(payload.customer_id || existing.customer_id),
    customer_name: customer.name || '',
    items,
    notes: payload.notes ?? existing.notes,
    payment_terms_days: paymentTerms,
    service_date: payload.service_date ?? existing.service_date,
    due_date: dueDate,
    related_document_id: payload.related_document_id ? normalizeId(payload.related_document_id) : '',
    totals: {
      ...existing.totals,
      net: calculated.net,
      vat: company.is_kleinunternehmer ? 0 : calculated.vat,
      gross: calculated.gross,
      remaining_amount: Math.max(0, calculated.gross - asNumber(existing.totals?.paid_amount, 0)),
    },
    is_kleinunternehmer: company.is_kleinunternehmer,
    total_gross: calculated.gross,
    updated_at: nowIso(),
  }

  await db.documents.update(Number(id), nextData)
  return { id: String(id), ...nextData }
}

export async function updateStatus(id, status) {
  const document = await db.documents.get(Number(id))
  if (!document) throw new Error('Dokument nicht gefunden')
  assertStatusTransition(document.document_type, document.status, status)

  const updated = { ...document, status, updated_at: nowIso() }
  await db.documents.update(Number(id), updated)
  return { id: String(id), ...updated }
}

export async function addPayment(id, payload) {
  const document = await db.documents.get(Number(id))
  if (!document) throw new Error('Dokument nicht gefunden')
  if (!['INVOICE', 'PARTIAL_INVOICE'].includes(document.document_type)) throw new Error('Zahlung nur bei Rechnungen möglich')
  if (['DRAFT', 'CANCELLED', 'PAID'].includes(document.status)) throw new Error('Zahlung für diesen Status nicht erlaubt')

  const amount = asNumber(payload.amount, 0)
  if (amount <= 0) throw new Error('Betrag muss größer 0 sein')
  const remaining = asNumber(document.totals?.remaining_amount, 0)
  if (amount > remaining + MONEY_EPSILON) throw new Error('Betrag überschreitet Restbetrag')

  const paidAmount = +(asNumber(document.totals?.paid_amount, 0) + amount).toFixed(2)
  const gross = asNumber(document.totals?.gross, 0)
  const remainingAmount = Math.max(0, +(gross - paidAmount).toFixed(2))
  const nextStatus = Math.abs(paidAmount - gross) < MONEY_EPSILON ? 'PAID' : 'PARTIALLY_PAID'

  const payment = {
    amount,
    method: payload.method || payload.payment_method || 'BANK',
    note: payload.note || '',
    date: nowIso(),
  }

  const updated = {
    ...document,
    payments: [...(document.payments || []), payment],
    status: nextStatus,
    totals: { ...document.totals, paid_amount: paidAmount, remaining_amount: remainingAmount },
    updated_at: nowIso(),
  }
  await db.documents.update(Number(id), updated)
  return { id: String(id), ...updated }
}

export async function addReminder(id, payload) {
  const document = await db.documents.get(Number(id))
  if (!document) throw new Error('Dokument nicht gefunden')
  if (!['INVOICE', 'PARTIAL_INVOICE'].includes(document.document_type)) throw new Error('Mahnung nur bei Rechnungen möglich')
  if (!['SENT', 'OVERDUE', 'PARTIALLY_PAID'].includes(document.status)) throw new Error('Mahnung für diesen Status nicht erlaubt')

  const nextLevel = (document.reminders?.length || 0) + 1
  if (nextLevel > MAX_REMINDER_LEVEL) throw new Error('Maximale Mahnstufe erreicht')

  const reminder = {
    level: nextLevel,
    fee: asNumber(payload.fee, 0),
    note: payload.note || '',
    sent_at: nowIso(),
  }

  const updated = {
    ...document,
    reminders: [...(document.reminders || []), reminder],
    status: document.status === 'OVERDUE' ? 'OVERDUE' : 'OVERDUE',
    updated_at: nowIso(),
  }
  await db.documents.update(Number(id), updated)
  return { id: String(id), ...updated }
}

export async function listRelatedDocuments(id) {
  const current = await db.documents.get(Number(id))
  if (!current) return { parent: null, children: [] }

  const parent = current.related_document_id ? await db.documents.get(Number(current.related_document_id)) : null
  const children = await db.documents.where('related_document_id').equals(normalizeId(id)).toArray()

  return {
    parent: parent ? { id: String(parent.id), ...parent, gross: parent.totals?.gross ?? 0 } : null,
    children: children.map((child) => ({ id: String(child.id), ...child, gross: child.totals?.gross ?? 0 })),
  }
}

export async function cancelDocument(id) {
  const source = await db.documents.get(Number(id))
  if (!source) throw new Error('Dokument nicht gefunden')
  if (!['INVOICE', 'PARTIAL_INVOICE'].includes(source.document_type)) throw new Error('Nur Rechnungen können storniert werden')
  if (source.status === 'CANCELLED') throw new Error('Dokument ist bereits storniert')

  const cancellation = await createDocument({
    document_type: 'CANCELLATION',
    customer_id: source.customer_id,
    items: source.items.map((item) => ({ ...item })),
    notes: `Storno zu ${source.document_number}${source.notes ? `\n${source.notes}` : ''}`,
    payment_terms_days: 0,
    related_document_id: normalizeId(id),
  })

  await db.documents.update(Number(cancellation.id), {
    ...cancellation,
    status: 'SENT',
    totals: {
      ...cancellation.totals,
      net: -Math.abs(cancellation.totals.net),
      vat: -Math.abs(cancellation.totals.vat),
      gross: -Math.abs(cancellation.totals.gross),
      remaining_amount: -Math.abs(cancellation.totals.gross),
    },
    total_gross: -Math.abs(cancellation.totals.gross),
    updated_at: nowIso(),
  })

  await db.documents.update(Number(id), { ...source, status: 'CANCELLED', updated_at: nowIso() })
  const storedCancellation = await db.documents.get(Number(cancellation.id))
  return { id: String(storedCancellation.id), ...storedCancellation }
}

export async function createCreditNote(id) {
  const source = await db.documents.get(Number(id))
  if (!source) throw new Error('Dokument nicht gefunden')
  if (!['INVOICE', 'PARTIAL_INVOICE'].includes(source.document_type)) throw new Error('Nur Rechnungen können gutgeschrieben werden')
  if (source.status === 'CANCELLED') throw new Error('Stornierte Dokumente können nicht gutgeschrieben werden')

  const credit = await createDocument({
    document_type: 'CREDIT_NOTE',
    customer_id: source.customer_id,
    items: source.items.map((item) => ({ ...item })),
    notes: `Gutschrift zu ${source.document_number}${source.notes ? `\n${source.notes}` : ''}`,
    payment_terms_days: 0,
    related_document_id: normalizeId(id),
  })

  await db.documents.update(Number(credit.id), {
    ...credit,
    status: 'SENT',
    totals: {
      ...credit.totals,
      net: -Math.abs(credit.totals.net),
      vat: -Math.abs(credit.totals.vat),
      gross: -Math.abs(credit.totals.gross),
      remaining_amount: -Math.abs(credit.totals.gross),
    },
    total_gross: -Math.abs(credit.totals.gross),
    updated_at: nowIso(),
  })

  const storedCredit = await db.documents.get(Number(credit.id))
  return { id: String(storedCredit.id), ...storedCredit }
}

export async function convertQuoteToInvoice(id) {
  const quote = await db.documents.get(Number(id))
  if (!quote) throw new Error('Dokument nicht gefunden')
  if (quote.document_type !== 'QUOTE') throw new Error('Nur Angebote können umgewandelt werden')
  if (quote.status !== 'ACCEPTED') throw new Error('Nur akzeptierte Angebote können umgewandelt werden')

  const invoice = await createDocument({
    document_type: 'INVOICE',
    customer_id: quote.customer_id,
    items: quote.items.map((item) => ({ ...item })),
    notes: quote.notes || '',
    payment_terms_days: quote.payment_terms_days || 14,
    service_date: quote.service_date || '',
    related_document_id: normalizeId(id),
  })

  await db.documents.update(Number(id), { ...quote, status: 'CONVERTED', updated_at: nowIso() })
  return invoice
}

export async function createPartialInvoice(id, payload) {
  const source = await db.documents.get(Number(id))
  if (!source) throw new Error('Dokument nicht gefunden')
  if (source.document_type !== 'INVOICE') throw new Error('Teilrechnung nur von Rechnung möglich')
  if (source.status === 'CANCELLED') throw new Error('Stornierte Rechnung kann nicht aufgeteilt werden')

  const amount = asNumber(payload.amount, 0)
  if (amount <= 0) throw new Error('Betrag muss positiv sein')

  const existingPartials = await db.documents.where('related_document_id').equals(normalizeId(id)).toArray()
  const partialsGross = existingPartials
    .filter((entry) => entry.document_type === 'PARTIAL_INVOICE')
    .reduce((sum, entry) => sum + Math.abs(asNumber(entry.totals?.gross, 0)), 0)
  const sourceGross = Math.abs(asNumber(source.totals?.gross, 0))
  if (partialsGross + amount > sourceGross + MONEY_EPSILON) {
    throw new Error('Summe der Abschlagsrechnungen überschreitet Ursprungsbetrag')
  }

  const vatRate = asNumber(source.items?.[0]?.vat_rate, 0.19)
  const isKleinunternehmer = !!source.is_kleinunternehmer
  const netAmount = isKleinunternehmer ? amount : +(amount / (1 + vatRate)).toFixed(2)
  const unitPrice = netAmount

  return createDocument({
    document_type: 'PARTIAL_INVOICE',
    customer_id: source.customer_id,
    items: [
      {
        name: `Abschlagsrechnung zu ${source.document_number}`,
        description: payload.notes || '',
        quantity: 1,
        unit: 'Pauschal',
        unit_price: unitPrice,
        vat_rate: isKleinunternehmer ? 0 : vatRate,
        discount_percent: 0,
      },
    ],
    notes: payload.notes || '',
    payment_terms_days: source.payment_terms_days || 14,
    related_document_id: normalizeId(id),
  })
}
