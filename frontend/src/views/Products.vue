<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useProductsStore } from '@/store/products'
import { formatCurrency } from '@/utils/helpers'
import DataTable from '@/components/DataTable.vue'

const router = useRouter()
const store = useProductsStore()
const searchInput = ref('')
let debounceTimer = null

const columns = [
  { key: 'article_number', label: 'Art.-Nr.', sortable: true },
  { key: 'name', label: 'Name', sortable: true },
  { key: 'unit_price', label: 'Preis', sortable: true, class: 'text-right' },
  { key: 'unit', label: 'Einheit' },
  { key: 'vat_rate', label: 'MwSt.' },
]

onMounted(() => {
  store.fetchProducts()
})

watch(searchInput, (val) => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    store.search = val
    store.page = 1
    store.fetchProducts()
  }, 300)
})

function onPageChange(p) {
  store.page = p
  store.fetchProducts({ page: p })
}

function openProduct(row) {
  router.push(`/products/${row.id}`)
}

async function handleDelete(row) {
  if (!confirm(`Produkt "${row.name}" wirklich löschen?`)) return
  await store.deleteProduct(row.id)
  store.fetchProducts()
}
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Produkte</h2>
        <p class="text-sm text-gray-500 mt-1">Artikel und Dienstleistungen verwalten</p>
      </div>
      <router-link to="/products/new" class="btn-primary">
        + Neues Produkt
      </router-link>
    </div>

    <div class="mb-4">
      <input
        v-model="searchInput"
        type="text"
        class="input-field max-w-sm"
        placeholder="Produkt suchen..."
      />
    </div>

    <DataTable
      :columns="columns"
      :rows="store.products"
      :total="store.total"
      :page="store.page"
      :page-size="store.pageSize"
      :loading="store.loading"
      @update:page="onPageChange"
      @row-click="openProduct"
    >
      <template #cell-unit_price="{ value }">
        {{ formatCurrency(value) }}
      </template>
      <template #cell-vat_rate="{ value }">
        {{ value != null ? (value * 100).toFixed(0) + '%' : '—' }}
      </template>
      <template #actions="{ row }">
        <div class="flex gap-2">
          <router-link :to="`/products/${row.id}`" class="text-primary-600 hover:text-primary-800 text-sm font-medium">
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
