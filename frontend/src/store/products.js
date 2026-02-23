import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'

export const useProductsStore = defineStore('products', () => {
  const products = ref([])
  const currentProduct = ref(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const search = ref('')

  /**
   * Fetch paginated product list.
   * @param {{ page?: number, limit?: number, search?: string }} params
   */
  async function fetchProducts(params = {}) {
    loading.value = true
    try {
      const query = {
        skip: ((params.page || page.value) - 1) * (params.limit || pageSize.value),
        limit: params.limit || pageSize.value,
      }
      if (params.search || search.value) query.search = params.search || search.value
      const { data } = await api.get('/products/', { params: query })
      products.value = data.items || data
      total.value = data.total ?? products.value.length
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch single product by id.
   * @param {string} id
   */
  async function fetchProduct(id) {
    loading.value = true
    try {
      const { data } = await api.get(`/products/${id}`)
      currentProduct.value = data
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new product.
   * @param {object} payload
   */
  async function createProduct(payload) {
    const { data } = await api.post('/products/', payload)
    return data
  }

  /**
   * Update an existing product.
   * @param {string} id
   * @param {object} payload
   */
  async function updateProduct(id, payload) {
    const { data } = await api.patch(`/products/${id}`, payload)
    return data
  }

  /**
   * Delete a product.
   * @param {string} id
   */
  async function deleteProduct(id) {
    await api.delete(`/products/${id}`)
  }

  return {
    products, currentProduct, total, page, pageSize, loading, search,
    fetchProducts, fetchProduct, createProduct, updateProduct, deleteProduct,
  }
})
