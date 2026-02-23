<script setup>
import { ref } from 'vue'
import { formatCurrency, formatDate } from '@/utils/helpers'

defineProps({
  /** @type {{ amount: number, payment_method: string, paid_at: string, note?: string }[]} */
  payments: { type: Array, default: () => [] },
  editable: { type: Boolean, default: false },
})

const emit = defineEmits(['add-payment'])

const PAYMENT_METHODS = [
  { value: 'BANK', label: 'Überweisung' },
  { value: 'CASH', label: 'Bar' },
  { value: 'PAYPAL', label: 'PayPal' },
]

const showForm = ref(false)
const newPayment = ref({ amount: 0, method: 'BANK', note: '' })

function submit() {
  if (newPayment.value.amount <= 0) return
  emit('add-payment', { ...newPayment.value })
  newPayment.value = { amount: 0, method: 'BANK', note: '' }
  showForm.value = false
}

function methodLabel(val) {
  return PAYMENT_METHODS.find((m) => m.value === val)?.label || val
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-gray-700">Zahlungen</h3>
      <button
        v-if="editable && !showForm"
        class="btn-secondary btn-sm"
        @click="showForm = true"
      >
        + Zahlung erfassen
      </button>
    </div>

    <!-- Add payment form -->
    <div v-if="showForm" class="mb-4 rounded-lg border border-gray-200 bg-gray-50 p-4 space-y-3">
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label class="label-text">Betrag (€)</label>
          <input v-model.number="newPayment.amount" type="number" step="0.01" min="0.01" class="input-field" />
        </div>
        <div>
          <label class="label-text">Zahlungsart</label>
          <select v-model="newPayment.method" class="input-field">
            <option v-for="m in PAYMENT_METHODS" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </div>
        <div>
          <label class="label-text">Notiz</label>
          <input v-model="newPayment.note" type="text" class="input-field" placeholder="Optional" />
        </div>
      </div>
      <div class="flex gap-2">
        <button class="btn-primary btn-sm" @click="submit">Speichern</button>
        <button class="btn-secondary btn-sm" @click="showForm = false">Abbrechen</button>
      </div>
    </div>

    <!-- Payment list -->
    <table v-if="payments.length > 0" class="min-w-full divide-y divide-gray-200 text-sm">
      <thead class="bg-gray-50">
        <tr>
          <th class="px-3 py-2 text-left font-semibold text-gray-600">Datum</th>
          <th class="px-3 py-2 text-right font-semibold text-gray-600">Betrag</th>
          <th class="px-3 py-2 text-left font-semibold text-gray-600">Zahlungsart</th>
          <th class="px-3 py-2 text-left font-semibold text-gray-600">Hinweis</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100">
        <tr v-for="(p, idx) in payments" :key="idx" class="hover:bg-gray-50">
          <td class="px-3 py-2">{{ formatDate(p.date || p.paid_at) }}</td>
          <td class="px-3 py-2 text-right font-medium text-green-700">{{ formatCurrency(p.amount) }}</td>
          <td class="px-3 py-2">{{ methodLabel(p.method || p.payment_method) }}</td>
          <td class="px-3 py-2 text-gray-600">
            <span v-if="p.reference" class="font-medium">{{ p.reference }}</span>
            <span v-else>{{ p.note || '—' }}</span>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else class="text-sm text-gray-400">Keine Zahlungen vorhanden</p>
  </div>
</template>
