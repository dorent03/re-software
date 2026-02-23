import { defineStore } from 'pinia'
import { ref } from 'vue'
import { db, nowIso } from '@/db'

export const useProductsStore = defineStore('products', () => {
  const products = ref([])
  const currentProduct = ref(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const search = ref('')

  /**
   * Fetch paginated product list from IndexedDB.
   * @param {{ page?: number, limit?: number, search?: string }} params
   */
  async function fetchProducts(params = {}) {
    loading.value = true
    try {
      const pageNum = Number(params.page || page.value)
      const limit = Number(params.limit || pageSize.value)
      const querySearch = String(params.search ?? search.value ?? '').trim().toLowerCase()
      const allProducts = await db.products.toArray()
      const activeProducts = allProducts.filter((entry) => entry.is_active !== false)
      const filtered = querySearch
        ? activeProducts.filter((entry) => {
            const values = [entry.name, entry.article_number, entry.description, entry.unit]
              .map((value) => String(value || '').toLowerCase())
            return values.some((value) => value.includes(querySearch))
          })
        : activeProducts

      total.value = filtered.length
      const start = (pageNum - 1) * limit
      products.value = filtered.slice(start, start + limit).map((entry) => ({ ...entry, id: String(entry.id) }))
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch single product by id from IndexedDB.
   * @param {string} id
   */
  async function fetchProduct(id) {
    loading.value = true
    try {
      const data = await db.products.get(Number(id))
      currentProduct.value = data ? { ...data, id: String(data.id) } : null
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new product in IndexedDB.
   * @param {object} payload
   */
  async function createProduct(payload) {
    const now = nowIso()
    const id = await db.products.add({
      ...payload,
      is_active: true,
      created_at: now,
      updated_at: now,
    })
    const created = await db.products.get(id)
    return { ...created, id: String(created.id) }
  }

  /**
   * Update an existing product in IndexedDB.
   * @param {string} id
   * @param {object} payload
   */
  async function updateProduct(id, payload) {
    const current = await db.products.get(Number(id))
    if (!current) throw new Error('Produkt nicht gefunden')
    const updated = { ...current, ...payload, updated_at: nowIso() }
    await db.products.update(Number(id), updated)
    return { ...updated, id: String(id) }
  }

  /**
   * Soft-delete a product.
   * @param {string} id
   */
  async function deleteProduct(id) {
    const current = await db.products.get(Number(id))
    if (!current) return
    await db.products.update(Number(id), { ...current, is_active: false, updated_at: nowIso() })
  }

  return {
    products, currentProduct, total, page, pageSize, loading, search,
    fetchProducts, fetchProduct, createProduct, updateProduct, deleteProduct,
  }
})
