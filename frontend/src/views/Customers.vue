<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useCustomersStore } from '@/store/customers'
import DataTable from '@/components/DataTable.vue'

const router = useRouter()
const store = useCustomersStore()
const searchInput = ref('')
let debounceTimer = null

const columns = [
  { key: 'customer_number', label: 'Kd.-Nr.', sortable: true },
  { key: 'name', label: 'Name', sortable: true },
  { key: 'email', label: 'E-Mail' },
  { key: 'phone', label: 'Telefon' },
  { key: 'city', label: 'Stadt' },
]

onMounted(() => {
  store.fetchCustomers()
})

watch(searchInput, (val) => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    store.search = val
    store.page = 1
    store.fetchCustomers()
  }, 300)
})

function onPageChange(p) {
  store.page = p
  store.fetchCustomers({ page: p })
}

function openCustomer(row) {
  router.push(`/customers/${row.id}`)
}

async function handleDelete(row) {
  if (!confirm(`Kunde "${row.name}" wirklich löschen?`)) return
  await store.deleteCustomer(row.id)
  store.fetchCustomers()
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Kunden</h2>
        <p class="text-sm text-gray-500 mt-1">Verwalten Sie Ihre Kundenliste</p>
      </div>
      <router-link to="/customers/new" class="btn-primary">
        + Neuer Kunde
      </router-link>
    </div>

    <!-- Search -->
    <div class="mb-4">
      <input
        v-model="searchInput"
        type="text"
        class="input-field max-w-sm"
        placeholder="Kunden suchen..."
      />
    </div>

    <!-- Table -->
    <DataTable
      :columns="columns"
      :rows="store.customers"
      :total="store.total"
      :page="store.page"
      :page-size="store.pageSize"
      :loading="store.loading"
      @update:page="onPageChange"
      @row-click="openCustomer"
    >
      <template #actions="{ row }">
        <div class="flex gap-2">
          <router-link :to="`/customers/${row.id}`" class="text-primary-600 hover:text-primary-800 text-sm font-medium">
            Bearbeiten
          </router-link>
          <button class="text-red-600 hover:text-red-800 text-sm font-medium" @click.stop="handleDelete(row)">
            Löschen
          </button>
        </div>
      </template>
    </DataTable>
  </div>
</template>
