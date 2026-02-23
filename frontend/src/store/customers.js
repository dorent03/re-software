import { defineStore } from 'pinia'
import { ref } from 'vue'
import { db, nowIso } from '@/db'

export const useCustomersStore = defineStore('customers', () => {
  const customers = ref([])
  const currentCustomer = ref(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const search = ref('')

  /**
   * Fetch paginated customer list from IndexedDB.
   * @param {{ page?: number, limit?: number, search?: string }} params
   */
  async function fetchCustomers(params = {}) {
    loading.value = true
    try {
      const pageNum = Number(params.page || page.value)
      const limit = Number(params.limit || pageSize.value)
      const querySearch = String(params.search ?? search.value ?? '').trim().toLowerCase()
      const allCustomers = await db.customers.toArray()
      const activeCustomers = allCustomers.filter((entry) => entry.is_active !== false)
      const filtered = querySearch
        ? activeCustomers.filter((entry) => {
            const values = [entry.name, entry.email, entry.phone, entry.city, entry.customer_number]
              .map((value) => String(value || '').toLowerCase())
            return values.some((value) => value.includes(querySearch))
          })
        : activeCustomers

      total.value = filtered.length
      const start = (pageNum - 1) * limit
      customers.value = filtered.slice(start, start + limit).map((entry) => ({ ...entry, id: String(entry.id) }))
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch single customer by id from IndexedDB.
   * @param {string} id
   */
  async function fetchCustomer(id) {
    loading.value = true
    try {
      const data = await db.customers.get(Number(id))
      currentCustomer.value = data ? { ...data, id: String(data.id) } : null
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new customer in IndexedDB.
   * @param {object} payload
   */
  async function createCustomer(payload) {
    const now = nowIso()
    const existingCustomers = await db.customers.toArray()
    const nextNumber = existingCustomers.length + 1
    const id = await db.customers.add({
      ...payload,
      customer_number: payload.customer_number || `CUST-${String(nextNumber).padStart(6, '0')}`,
      is_active: true,
      created_at: now,
      updated_at: now,
    })
    const created = await db.customers.get(id)
    return { ...created, id: String(created.id) }
  }

  /**
   * Update an existing customer in IndexedDB.
   * @param {string} id
   * @param {object} payload
   */
  async function updateCustomer(id, payload) {
    const current = await db.customers.get(Number(id))
    if (!current) throw new Error('Kunde nicht gefunden')
    const updated = { ...current, ...payload, updated_at: nowIso() }
    await db.customers.update(Number(id), updated)
    return { ...updated, id: String(id) }
  }

  /**
   * Soft-delete a customer.
   * @param {string} id
   */
  async function deleteCustomer(id) {
    const current = await db.customers.get(Number(id))
    if (!current) return
    await db.customers.update(Number(id), { ...current, is_active: false, updated_at: nowIso() })
  }

  return {
    customers, currentCustomer, total, page, pageSize, loading, search,
    fetchCustomers, fetchCustomer, createCustomer, updateCustomer, deleteCustomer,
  }
})
