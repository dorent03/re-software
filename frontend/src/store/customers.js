import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'

export const useCustomersStore = defineStore('customers', () => {
  const customers = ref([])
  const currentCustomer = ref(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const search = ref('')

  /**
   * Fetch paginated customer list.
   * @param {{ page?: number, limit?: number, search?: string }} params
   */
  async function fetchCustomers(params = {}) {
    loading.value = true
    try {
      const query = {
        skip: ((params.page || page.value) - 1) * (params.limit || pageSize.value),
        limit: params.limit || pageSize.value,
      }
      if (params.search || search.value) query.search = params.search || search.value
      const { data } = await api.get('/customers/', { params: query })
      customers.value = data.items || data
      total.value = data.total ?? customers.value.length
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch single customer by id.
   * @param {string} id
   */
  async function fetchCustomer(id) {
    loading.value = true
    try {
      const { data } = await api.get(`/customers/${id}`)
      currentCustomer.value = data
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new customer.
   * @param {object} payload
   */
  async function createCustomer(payload) {
    const { data } = await api.post('/customers/', payload)
    return data
  }

  /**
   * Update an existing customer.
   * @param {string} id
   * @param {object} payload
   */
  async function updateCustomer(id, payload) {
    const { data } = await api.patch(`/customers/${id}`, payload)
    return data
  }

  /**
   * Soft-delete a customer.
   * @param {string} id
   */
  async function deleteCustomer(id) {
    await api.delete(`/customers/${id}`)
  }

  return {
    customers, currentCustomer, total, page, pageSize, loading, search,
    fetchCustomers, fetchCustomer, createCustomer, updateCustomer, deleteCustomer,
  }
})
