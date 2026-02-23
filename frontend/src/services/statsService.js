import { db } from '@/db'

function safeYear(value) {
  const parsed = Number(value)
  return Number.isInteger(parsed) ? parsed : new Date().getFullYear()
}

function dateYear(dateValue) {
  const parsed = new Date(dateValue)
  return Number.isNaN(parsed.getTime()) ? null : parsed.getFullYear()
}

function dateMonth(dateValue) {
  const parsed = new Date(dateValue)
  return Number.isNaN(parsed.getTime()) ? null : parsed.getMonth() + 1
}

export async function getMonthlyRevenue(year) {
  const selectedYear = safeYear(year)
  const documents = await db.documents.toArray()
  const groups = new Map()

  documents
    .filter((entry) => entry.document_type === 'INVOICE' && entry.status === 'PAID')
    .filter((entry) => dateYear(entry.issue_date || entry.created_at) === selectedYear)
    .forEach((entry) => {
      const month = dateMonth(entry.issue_date || entry.created_at)
      if (!month) return
      const key = `${selectedYear}-${String(month).padStart(2, '0')}`
      if (!groups.has(key)) {
        groups.set(key, {
          year: selectedYear,
          month,
          total_gross: 0,
          total_net: 0,
          total_vat: 0,
          invoice_count: 0,
        })
      }
      const current = groups.get(key)
      current.total_gross += Number(entry.totals?.gross || 0)
      current.total_net += Number(entry.totals?.net || 0)
      current.total_vat += Number(entry.totals?.vat || 0)
      current.invoice_count += 1
    })

  return Array.from(groups.values())
    .sort((a, b) => a.month - b.month)
    .map((item) => ({
      ...item,
      total_gross: +item.total_gross.toFixed(2),
      total_net: +item.total_net.toFixed(2),
      total_vat: +item.total_vat.toFixed(2),
    }))
}

export async function getRevenueByCustomer(year) {
  const selectedYear = safeYear(year)
  const documents = await db.documents.toArray()
  const customers = await db.customers.toArray()
  const customerMap = new Map(customers.map((customer) => [String(customer.id), customer.name || String(customer.id)]))
  const groups = new Map()

  documents
    .filter((entry) => entry.document_type === 'INVOICE' && entry.status === 'PAID')
    .filter((entry) => dateYear(entry.issue_date || entry.created_at) === selectedYear)
    .forEach((entry) => {
      const customerId = String(entry.customer_id)
      if (!groups.has(customerId)) {
        groups.set(customerId, {
          customer_id: customerId,
          customer_name: customerMap.get(customerId) || customerId,
          total_gross: 0,
          total_net: 0,
          invoice_count: 0,
        })
      }
      const current = groups.get(customerId)
      current.total_gross += Number(entry.totals?.gross || 0)
      current.total_net += Number(entry.totals?.net || 0)
      current.invoice_count += 1
    })

  return Array.from(groups.values())
    .sort((a, b) => b.total_gross - a.total_gross)
    .map((item) => ({
      ...item,
      total_gross: +item.total_gross.toFixed(2),
      total_net: +item.total_net.toFixed(2),
    }))
}
