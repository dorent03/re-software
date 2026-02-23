<script setup>
import { ref, onMounted, computed } from 'vue'
import { useStatsStore } from '@/store/stats'
import { useDocumentsStore } from '@/store/documents'
import { formatCurrency } from '@/utils/helpers'
import ChartRevenue from '@/components/ChartRevenue.vue'

const statsStore = useStatsStore()
const docStore = useDocumentsStore()

const selectedYear = ref(new Date().getFullYear())
const loading = ref(true)

onMounted(async () => {
  try {
    await Promise.all([
      statsStore.fetchMonthlyRevenue(selectedYear.value),
      statsStore.fetchCustomerRevenue(selectedYear.value),
      docStore.fetchDocuments({ page: 1, limit: 100 }),
    ])
  } catch (err) {
    console.error('Dashboard load failed:', err)
  } finally {
    loading.value = false
  }
})

async function changeYear(year) {
  selectedYear.value = year
  await Promise.all([
    statsStore.fetchMonthlyRevenue(year),
    statsStore.fetchCustomerRevenue(year),
  ])
}

const totalRevenue = computed(() => {
  const arr = Array.isArray(statsStore.monthlyRevenue) ? statsStore.monthlyRevenue : []
  return arr.reduce((sum, m) => sum + (m.total_gross ?? m.total ?? 0), 0)
})

const documentList = computed(() => Array.isArray(docStore.documents) ? docStore.documents : [])

const openInvoices = computed(() =>
  documentList.value.filter((d) =>
    d.document_type === 'INVOICE' && ['SENT', 'OVERDUE', 'PARTIALLY_PAID'].includes(d.status)
  ).length
)

const paidInvoices = computed(() =>
  documentList.value.filter((d) => d.document_type === 'INVOICE' && d.status === 'PAID').length
)

const overdueInvoices = computed(() =>
  documentList.value.filter((d) => d.document_type === 'INVOICE' && d.status === 'OVERDUE').length
)

const topCustomers = computed(() => {
  const arr = Array.isArray(statsStore.customerRevenue) ? statsStore.customerRevenue : []
  return [...arr]
    .sort((a, b) => (b.total_gross ?? b.total ?? 0) - (a.total_gross ?? a.total ?? 0))
    .slice(0, 5)
})

const years = computed(() => {
  const current = new Date().getFullYear()
  return [current, current - 1, current - 2]
})
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Dashboard</h2>
        <p class="text-sm text-gray-500 mt-1">Übersicht über Ihr Geschäft</p>
      </div>
      <div class="flex gap-2">
        <button
          v-for="year in years"
          :key="year"
          :class="[
            'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
            year === selectedYear ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
          ]"
          @click="changeYear(year)"
        >
          {{ year }}
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <svg class="animate-spin h-8 w-8 text-primary-500" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <template v-else>
      <!-- KPI Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div class="card">
          <p class="text-sm text-gray-500">Gesamtumsatz {{ selectedYear }}</p>
          <p class="text-2xl font-bold text-gray-900 mt-1">{{ formatCurrency(totalRevenue) }}</p>
        </div>
        <div class="card">
          <p class="text-sm text-gray-500">Offene Rechnungen</p>
          <p class="text-2xl font-bold text-yellow-600 mt-1">{{ openInvoices }}</p>
        </div>
        <div class="card">
          <p class="text-sm text-gray-500">Bezahlte Rechnungen</p>
          <p class="text-2xl font-bold text-green-600 mt-1">{{ paidInvoices }}</p>
        </div>
        <div class="card">
          <p class="text-sm text-gray-500">Überfällige Rechnungen</p>
          <p class="text-2xl font-bold text-red-600 mt-1">{{ overdueInvoices }}</p>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div class="card">
          <ChartRevenue :data="statsStore.monthlyRevenue" :title="`Monatlicher Umsatz ${selectedYear}`" />
        </div>

        <!-- Top Customers -->
        <div class="card">
          <h3 class="text-sm font-semibold text-gray-700 mb-4">Top Kunden nach Umsatz</h3>
          <div v-if="topCustomers.length === 0" class="text-sm text-gray-400 py-8 text-center">
            Keine Daten vorhanden
          </div>
          <div v-else class="space-y-3">
            <div
              v-for="(cust, idx) in topCustomers"
              :key="cust.customer_id || idx"
              class="flex items-center justify-between"
            >
              <div class="flex items-center gap-3">
                <span class="flex-shrink-0 w-7 h-7 rounded-full bg-primary-100 text-primary-700 text-xs font-bold flex items-center justify-center">
                  {{ idx + 1 }}
                </span>
                <span class="text-sm font-medium text-gray-800">{{ cust.customer_name || cust.customer_id }}</span>
              </div>
              <span class="text-sm font-semibold text-gray-700">{{ formatCurrency(cust.total_gross ?? cust.total) }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
