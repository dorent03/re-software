<script setup>
import { ref } from 'vue'
import { formatCurrency, formatDate } from '@/utils/helpers'

defineProps({
  /** @type {{ level: number, fee: number, sent_at: string, note?: string }[]} */
  reminders: { type: Array, default: () => [] },
  editable: { type: Boolean, default: false },
})

const emit = defineEmits(['add-reminder'])

const showForm = ref(false)
const newReminder = ref({ fee: 0, note: '' })

function submit() {
  emit('add-reminder', { ...newReminder.value })
  newReminder.value = { fee: 0, note: '' }
  showForm.value = false
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-gray-700">Mahnungen</h3>
      <button
        v-if="editable && !showForm"
        class="btn-secondary btn-sm"
        @click="showForm = true"
      >
        + Mahnung erstellen
      </button>
    </div>

    <!-- Add reminder form -->
    <div v-if="showForm" class="mb-4 rounded-lg border border-gray-200 bg-gray-50 p-4 space-y-3">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="label-text">Mahngebühr (€)</label>
          <input v-model.number="newReminder.fee" type="number" step="0.01" min="0" class="input-field" />
        </div>
        <div>
          <label class="label-text">Notiz</label>
          <input v-model="newReminder.note" type="text" class="input-field" placeholder="Optional" />
        </div>
      </div>
      <div class="flex gap-2">
        <button class="btn-primary btn-sm" @click="submit">Senden</button>
        <button class="btn-secondary btn-sm" @click="showForm = false">Abbrechen</button>
      </div>
    </div>

    <!-- Reminder list -->
    <table v-if="reminders.length > 0" class="min-w-full divide-y divide-gray-200 text-sm">
      <thead class="bg-gray-50">
        <tr>
          <th class="px-3 py-2 text-left font-semibold text-gray-600">Stufe</th>
          <th class="px-3 py-2 text-left font-semibold text-gray-600">Datum</th>
          <th class="px-3 py-2 text-right font-semibold text-gray-600">Gebühr</th>
          <th class="px-3 py-2 text-left font-semibold text-gray-600">Notiz</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100">
        <tr v-for="(r, idx) in reminders" :key="idx" class="hover:bg-gray-50">
          <td class="px-3 py-2">
            <span class="badge" :class="r.level >= 3 ? 'badge-red' : r.level >= 2 ? 'badge-orange' : 'badge-yellow'">
              Stufe {{ r.level }}
            </span>
          </td>
          <td class="px-3 py-2">{{ formatDate(r.sent_at) }}</td>
          <td class="px-3 py-2 text-right">{{ formatCurrency(r.fee) }}</td>
          <td class="px-3 py-2 text-gray-500">{{ r.note || '—' }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else class="text-sm text-gray-400">Keine Mahnungen vorhanden</p>
  </div>
</template>
