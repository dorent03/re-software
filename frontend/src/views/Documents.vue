<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDocumentsStore } from '@/store/documents'
import { formatCurrency, formatDate, statusBadgeClass, documentTypeLabel } from '@/utils/helpers'
import DataTable from '@/components/DataTable.vue'

const router = useRouter()
const store = useDocumentsStore()
const searchInput = ref('')
let debounceTimer = null

const columns = [
  { key: 'document_number', label: 'Nr.', sortable: true },
  { key: 'document_type', label: 'Typ', sortable: true },
  { key: 'customer_name', label: 'Kunde', sortable: true },
  { key: 'status', label: 'Status' },
  { key: 'total_gross', label: 'Betrag', sortable: true, class: 'text-right' },
  { key: 'created_at', label: 'Erstellt', sortable: true },
]

const DOC_TYPES = [
  { value: '', label: 'Alle Typen' },
  { value: 'INVOICE', label: 'Rechnung' },
  { value: 'QUOTE', label: 'Angebot' },
  { value: 'DELIVERY_NOTE', label: 'Lieferschein' },
  { value: 'ORDER_CONFIRMATION', label: 'Auftragsbestätigung' },
  { value: 'PARTIAL_INVOICE', label: 'Abschlagsrechnung' },
  { value: 'CREDIT_NOTE', label: 'Gutschrift' },
  { value: 'CANCELLATION', label: 'Stornorechnung' },
]

const STATUSES = [
  { value: '', label: 'Alle Status' },
  { value: 'DRAFT', label: 'Entwurf' },
  { value: 'SENT', label: 'Gesendet' },
  { value: 'PAID', label: 'Bezahlt' },
  { value: 'PARTIALLY_PAID', label: 'Teilweise bezahlt' },
  { value: 'OVERDUE', label: 'Überfällig' },
  { value: 'CANCELLED', label: 'Storniert' },
  { value: 'ACCEPTED', label: 'Akzeptiert' },
  { value: 'REJECTED', label: 'Abgelehnt' },
  { value: 'CONVERTED', label: 'Umgewandelt' },
]

onMounted(() => {
  store.fetchDocuments()
})

watch(searchInput, (val) => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    store.search = val
    store.page = 1
    store.fetchDocuments()
  }, 300)
})

function onFilterType(val) {
  store.filterType = val
  store.page = 1
  store.fetchDocuments()
}

function onFilterStatus(val) {
  store.filterStatus = val
  store.page = 1
  store.fetchDocuments()
}

function onPageChange(p) {
  store.page = p
  store.fetchDocuments({ page: p })
}

function openDocument(row) {
  router.push(`/documents/${row.id}`)
}

async function handleDelete(row) {
  if (row.status !== 'DRAFT') {
    alert('Nur Entwürfe können gelöscht werden.')
    return
  }
  if (!confirm(`Dokument "${row.document_number}" wirklich löschen?`)) return
  await store.deleteDocument(row.id)
  store.fetchDocuments()
}
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
      <div>
        <h2 class="text-xl font-bold text-gray-900">Dokumente</h2>
        <p class="text-sm text-gray-500 mt-1">Rechnungen, Angebote und mehr</p>
      </div>
      <router-link to="/documents/new" class="btn-primary">
        + Neues Dokument
      </router-link>
    </div>

    <!-- Filters -->
    <div class="flex flex-col sm:flex-row gap-3 mb-4">
      <input
        v-model="searchInput"
        type="text"
        class="input-field max-w-xs"
        placeholder="Suchen..."
      />
      <select
        :value="store.filterType"
        class="input-field max-w-[200px]"
        @change="onFilterType($event.target.value)"
      >
        <option v-for="t in DOC_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
      </select>
      <select
        :value="store.filterStatus"
        class="input-field max-w-[200px]"
        @change="onFilterStatus($event.target.value)"
      >
        <option v-for="s in STATUSES" :key="s.value" :value="s.value">{{ s.label }}</option>
      </select>
    </div>

    <!-- Table -->
    <DataTable
      :columns="columns"
      :rows="store.documents"
      :total="store.total"
      :page="store.page"
      :page-size="store.pageSize"
      :loading="store.loading"
      @update:page="onPageChange"
      @row-click="openDocument"
    >
      <template #cell-document_type="{ value }">
        {{ documentTypeLabel(value) }}
      </template>
      <template #cell-status="{ value }">
        <span :class="['badge', statusBadgeClass(value)]">{{ value }}</span>
      </template>
      <template #cell-total_gross="{ row }">
        {{ formatCurrency(row.totals?.gross ?? row.total_gross) }}
      </template>
      <template #cell-created_at="{ value }">
        {{ formatDate(value) }}
      </template>
      <template #actions="{ row }">
        <div class="flex gap-2">
          <router-link :to="`/documents/${row.id}`" class="text-primary-600 hover:text-primary-800 text-sm font-medium">
            Öffnen
          </router-link>
          <router-link :to="`/documents/${row.id}/pdf`" class="text-gray-600 hover:text-gray-800 text-sm font-medium">
            PDF
          </router-link>
          <button
            v-if="row.status === 'DRAFT'"
            class="text-red-600 hover:text-red-800 text-sm font-medium"
            @click.stop="handleDelete(row)"
          >
            Löschen
          </button>
        </div>
      </template>
    </DataTable>
  </div>
</template>
