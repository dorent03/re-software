import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'

export const useStatsStore = defineStore('stats', () => {
  const monthlyRevenue = ref([])
  const customerRevenue = ref([])
  const loading = ref(false)

  /**
   * Fetch monthly revenue aggregation.
   * @param {number} [year] – defaults to current year
   */
  async function fetchMonthlyRevenue(year) {
    loading.value = true
    try {
      const params = {}
      if (year) params.year = year
      const { data } = await api.get('/stats/revenue/monthly', { params })
      monthlyRevenue.value = Array.isArray(data?.data) ? data.data : (data?.items ?? [])
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch revenue by customer.
   * @param {number} [year]
   */
  async function fetchCustomerRevenue(year) {
    loading.value = true
    try {
      const params = {}
      if (year) params.year = year
      const { data } = await api.get('/stats/revenue/by-customer', { params })
      customerRevenue.value = Array.isArray(data?.data) ? data.data : (data?.items ?? [])
    } finally {
      loading.value = false
    }
  }

  return { monthlyRevenue, customerRevenue, loading, fetchMonthlyRevenue, fetchCustomerRevenue }
})
