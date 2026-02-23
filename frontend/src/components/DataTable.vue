<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** @type {{ key: string, label: string, sortable?: boolean, class?: string }[]} */
  columns: { type: Array, required: true },
  /** @type {Array} */
  rows: { type: Array, default: () => [] },
  /** Total rows (for pagination) */
  total: { type: Number, default: 0 },
  /** Current page (1-based) */
  page: { type: Number, default: 1 },
  /** Rows per page */
  pageSize: { type: Number, default: 20 },
  /** Loading state */
  loading: { type: Boolean, default: false },
  /** Sortable key currently sorted by */
  sortKey: { type: String, default: '' },
  /** Sort direction */
  sortDir: { type: String, default: 'asc' },
})

const emit = defineEmits(['update:page', 'update:sortKey', 'update:sortDir', 'row-click'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
const pageStart = computed(() => (props.page - 1) * props.pageSize + 1)
const pageEnd = computed(() => Math.min(props.page * props.pageSize, props.total))

function goPage(p) {
  if (p >= 1 && p <= totalPages.value) {
    emit('update:page', p)
  }
}

function toggleSort(col) {
  if (!col.sortable) return
  if (props.sortKey === col.key) {
    emit('update:sortDir', props.sortDir === 'asc' ? 'desc' : 'asc')
  } else {
    emit('update:sortKey', col.key)
    emit('update:sortDir', 'asc')
  }
}

/** Visible pagination page numbers. */
const visiblePages = computed(() => {
  const pages = []
  const max = totalPages.value
  const current = props.page
  const range = 2
  for (let i = Math.max(1, current - range); i <= Math.min(max, current + range); i++) {
    pages.push(i)
  }
  return pages
})
</script>

<template>
  <div class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              :class="[
                'px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500',
                col.sortable ? 'cursor-pointer select-none hover:text-gray-700' : '',
                col.class || '',
              ]"
              @click="toggleSort(col)"
            >
              <div class="flex items-center gap-1">
                {{ col.label }}
                <template v-if="col.sortable && sortKey === col.key">
                  <svg class="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
                    <path v-if="sortDir === 'asc'" d="M5.293 9.707l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L10 7.414l-3.293 3.293a1 1 0 01-1.414-1.414z" />
                    <path v-else d="M14.707 10.293l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L10 12.586l3.293-3.293a1 1 0 111.414 1.414z" />
                  </svg>
                </template>
              </div>
            </th>
            <!-- Actions column -->
            <th v-if="$slots.actions" class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500">
              Aktionen
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <!-- Loading overlay -->
          <tr v-if="loading">
            <td :colspan="columns.length + ($slots.actions ? 1 : 0)" class="px-4 py-12 text-center text-sm text-gray-400">
              <svg class="animate-spin h-6 w-6 mx-auto text-primary-500" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span class="mt-2 block">Laden...</span>
            </td>
          </tr>
          <!-- Empty state -->
          <tr v-else-if="rows.length === 0">
            <td :colspan="columns.length + ($slots.actions ? 1 : 0)" class="px-4 py-12 text-center text-sm text-gray-400">
              Keine Daten vorhanden
            </td>
          </tr>
          <!-- Data rows -->
          <tr
            v-else
            v-for="(row, idx) in rows"
            :key="row.id || idx"
            class="hover:bg-gray-50 transition-colors cursor-pointer"
            @click="emit('row-click', row)"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              :class="['px-4 py-3 text-sm text-gray-700 whitespace-nowrap', col.class || '']"
            >
              <slot :name="'cell-' + col.key" :row="row" :value="row[col.key]">
                {{ row[col.key] ?? '—' }}
              </slot>
            </td>
            <td v-if="$slots.actions" class="px-4 py-3 text-right whitespace-nowrap">
              <slot name="actions" :row="row" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="total > pageSize" class="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-gray-200 bg-gray-50 px-4 py-3">
      <p class="text-sm text-gray-600">
        {{ pageStart }}–{{ pageEnd }} von {{ total }}
      </p>
      <nav class="flex items-center gap-1">
        <button
          class="rounded px-2 py-1 text-sm hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed"
          :disabled="page <= 1"
          @click="goPage(page - 1)"
        >
          &laquo;
        </button>
        <button
          v-for="p in visiblePages"
          :key="p"
          :class="[
            'rounded px-3 py-1 text-sm',
            p === page ? 'bg-primary-600 text-white' : 'hover:bg-gray-200',
          ]"
          @click="goPage(p)"
        >
          {{ p }}
        </button>
        <button
          class="rounded px-2 py-1 text-sm hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed"
          :disabled="page >= totalPages"
          @click="goPage(page + 1)"
        >
          &raquo;
        </button>
      </nav>
    </div>
  </div>
</template>
