import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getMonthlyRevenue, getRevenueByCustomer } from '@/services/statsService'

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
      monthlyRevenue.value = await getMonthlyRevenue(year)
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
      customerRevenue.value = await getRevenueByCustomer(year)
    } finally {
      loading.value = false
    }
  }

  return { monthlyRevenue, customerRevenue, loading, fetchMonthlyRevenue, fetchCustomerRevenue }
})
