<script setup>
import { ref, computed } from 'vue'
import { formatCurrency, calcLineItem } from '@/utils/helpers'

const props = defineProps({
  /** @type {{ description: string, quantity: number, unit: string, unit_price: number, vat_rate: number, discount_percent: number }[]} */
  positions: { type: Array, default: () => [] },
  /** Whether inline editing is enabled */
  editable: { type: Boolean, default: false },
  /** Available VAT rates */
  vatRates: { type: Array, default: () => [0.19, 0.07, 0] },
  /** Kleinunternehmer mode hides VAT column */
  kleinunternehmer: { type: Boolean, default: false },
})

const emit = defineEmits(['update:positions'])

const draggedIndex = ref(null)

function addRow() {
  const rows = [...props.positions, {
    product_id: '',
    name: '',
    description: '',
    quantity: 1,
    unit: 'Stück',
    unit_price: 0,
    vat_rate: props.kleinunternehmer ? 0 : (props.vatRates[0] || 0.19),
    discount_percent: 0,
  }]
  emit('update:positions', rows)
}

function updateRow(index, field, value) {
  const rows = [...props.positions]
  rows[index] = { ...rows[index], [field]: value }
  emit('update:positions', rows)
}

function removeRow(index) {
  const rows = props.positions.filter((_, i) => i !== index)
  emit('update:positions', rows)
}

function onDragStart(e, index) {
  draggedIndex.value = index
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', String(index))
  e.target.closest('tr')?.classList.add('opacity-50')
}

function onDragEnd(e) {
  e.target.closest('tr')?.classList.remove('opacity-50')
  draggedIndex.value = null
}

function onDragOver(e) {
  e.preventDefault()
  e.dataTransfer.dropEffect = 'move'
}

function onDrop(e, dropIndex) {
  e.preventDefault()
  const from = draggedIndex.value
  if (from == null || from === dropIndex) return
  const rows = [...props.positions]
  const [moved] = rows.splice(from, 1)
  rows.splice(dropIndex, 0, moved)
  emit('update:positions', rows)
  draggedIndex.value = null
}

const totalNet = computed(() => {
  return props.positions.reduce((sum, p) => sum + calcLineItem(p).net_amount, 0).toFixed(2)
})
</script>

<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200 text-sm">
      <thead class="bg-gray-50">
        <tr>
          <th v-if="editable" class="px-2 py-2 w-10 text-center font-semibold text-gray-600" title="Reihenfolge ändern" />
          <th class="px-3 py-2 text-left font-semibold text-gray-600">Pos.</th>
          <th class="px-3 py-2 text-left font-semibold text-gray-600">Name</th>
          <th class="px-3 py-2 text-left font-semibold text-gray-600">Beschreibung</th>
          <th class="px-3 py-2 text-right font-semibold text-gray-600 w-20">Menge</th>
          <th class="px-3 py-2 text-left font-semibold text-gray-600 w-20">Einheit</th>
          <th class="px-3 py-2 text-right font-semibold text-gray-600 w-28">Einzelpreis</th>
          <th class="px-3 py-2 text-right font-semibold text-gray-600 w-20">Rabatt %</th>
          <th v-if="!kleinunternehmer" class="px-3 py-2 text-right font-semibold text-gray-600 w-20">MwSt.</th>
          <th class="px-3 py-2 text-right font-semibold text-gray-600 w-28">Netto</th>
          <th v-if="editable" class="px-3 py-2 w-12"></th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100">
        <tr
          v-for="(pos, idx) in positions"
          :key="idx"
          class="hover:bg-gray-50 transition-colors"
          :class="{ 'bg-primary-50': draggedIndex === idx }"
          @dragover="editable ? onDragOver($event) : null"
          @drop="editable ? onDrop($event, idx) : null"
        >
          <td v-if="editable" class="px-2 py-2 text-center text-gray-400 cursor-grab active:cursor-grabbing" draggable="true" @dragstart="onDragStart($event, idx)" @dragend="onDragEnd">
            <svg class="h-4 w-4 inline-block" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M6 5h12v2H6V5zm0 6h12v2H6v-2zm0 6h12v2H6v-2z" />
            </svg>
          </td>
          <td class="px-3 py-2 text-gray-500">{{ idx + 1 }}</td>

          <!-- Name / Bezeichnung -->
          <td class="px-3 py-2">
            <input
              v-if="editable"
              :value="pos.name"
              class="input-field !py-1"
              placeholder="Name"
              @input="updateRow(idx, 'name', $event.target.value)"
            />
            <span v-else>{{ pos.name || pos.description || '—' }}</span>
          </td>

          <!-- Description -->
          <td class="px-3 py-2">
            <input
              v-if="editable"
              :value="pos.description"
              class="input-field !py-1"
              placeholder="Beschreibung (optional)"
              @input="updateRow(idx, 'description', $event.target.value)"
            />
            <span v-else class="text-gray-600">{{ pos.description || '—' }}</span>
          </td>

          <!-- Quantity -->
          <td class="px-3 py-2 text-right">
            <input
              v-if="editable"
              :value="pos.quantity"
              type="number"
              min="0.01"
              step="any"
              class="input-field !py-1 text-right w-20"
              @input="updateRow(idx, 'quantity', Number($event.target.value))"
            />
            <span v-else>{{ pos.quantity }}</span>
          </td>

          <!-- Unit -->
          <td class="px-3 py-2">
            <input
              v-if="editable"
              :value="pos.unit"
              class="input-field !py-1 w-20"
              @input="updateRow(idx, 'unit', $event.target.value)"
            />
            <span v-else>{{ pos.unit }}</span>
          </td>

          <!-- Unit price -->
          <td class="px-3 py-2 text-right">
            <input
              v-if="editable"
              :value="pos.unit_price"
              type="number"
              min="0"
              step="0.01"
              class="input-field !py-1 text-right w-28"
              @input="updateRow(idx, 'unit_price', Number($event.target.value))"
            />
            <span v-else>{{ formatCurrency(pos.unit_price) }}</span>
          </td>

          <!-- Discount -->
          <td class="px-3 py-2 text-right">
            <input
              v-if="editable"
              :value="pos.discount_percent"
              type="number"
              min="0"
              max="100"
              step="0.1"
              class="input-field !py-1 text-right w-20"
              @input="updateRow(idx, 'discount_percent', Number($event.target.value))"
            />
            <span v-else>{{ pos.discount_percent || 0 }}%</span>
          </td>

          <!-- VAT rate -->
          <td v-if="!kleinunternehmer" class="px-3 py-2 text-right">
            <select
              v-if="editable"
              :value="pos.vat_rate"
              class="input-field !py-1 w-20"
              @change="updateRow(idx, 'vat_rate', Number($event.target.value))"
            >
              <option v-for="rate in vatRates" :key="rate" :value="rate">{{ (rate * 100).toFixed(0) }}%</option>
            </select>
            <span v-else>{{ (pos.vat_rate * 100).toFixed(0) }}%</span>
          </td>

          <!-- Net total -->
          <td class="px-3 py-2 text-right font-medium">
            {{ formatCurrency(calcLineItem(pos).net_amount) }}
          </td>

          <!-- Remove -->
          <td v-if="editable" class="px-3 py-2 text-center">
            <button
              class="text-red-500 hover:text-red-700 transition-colors"
              title="Position entfernen"
              @click="removeRow(idx)"
            >
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </td>
        </tr>
      </tbody>
      <tfoot v-if="positions.length > 0">
        <tr class="bg-gray-50 font-semibold">
          <td :colspan="kleinunternehmer ? 7 : 8" class="px-3 py-2 text-right">Summe Netto:</td>
          <td class="px-3 py-2 text-right">{{ formatCurrency(Number(totalNet)) }}</td>
          <td v-if="editable"></td>
        </tr>
      </tfoot>
    </table>

    <button
      v-if="editable"
      class="mt-3 btn-secondary btn-sm"
      @click="addRow"
    >
      + Position hinzufügen
    </button>
  </div>
</template>
