import Dexie from 'dexie'

const DATABASE_NAME = 'reSoftwareLocal'

class ReSoftwareDatabase extends Dexie {
  constructor() {
    super(DATABASE_NAME)
    this.version(1).stores({
      company: '++id, name, updated_at',
      customers: '++id, name, email, city, is_active, created_at',
      products: '++id, name, article_number, is_active, created_at',
      documents: '++id, document_number, document_type, status, customer_id, related_document_id, issue_date, due_date, created_at',
      counters: '++id, key, value',
    })
  }
}

export const db = new ReSoftwareDatabase()

export function nowIso() {
  return new Date().toISOString()
}

export function toDateOnly(date = new Date()) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function normalizeId(value) {
  return String(value)
}
