<script setup>
import { computed } from 'vue'
import { formatCurrency, calcDocumentTotals, calcLineItem } from '@/utils/helpers'

const props = defineProps({
  /** @type {{ quantity: number, unit_price: number, vat_rate: number, discount_percent: number }[]} */
  positions: { type: Array, default: () => [] },
  /** Paid amount so far */
  paidAmount: { type: Number, default: 0 },
  /** Whether Kleinunternehmer mode is active */
  kleinunternehmer: { type: Boolean, default: false },
})

const totals = computed(() => calcDocumentTotals(props.positions, props.kleinunternehmer))

const remaining = computed(() => {
  const val = totals.value.gross - props.paidAmount
  return Math.max(0, +val.toFixed(2))
})

/** VAT breakdown grouped by rate. */
const vatBreakdown = computed(() => {
  if (props.kleinunternehmer) return []
  const map = {}
  for (const pos of props.positions) {
    const { net_amount, vat_amount } = calcLineItem(pos)
    const key = pos.vat_rate
    if (!map[key]) map[key] = { rate: key, net: 0, vat: 0 }
    map[key].net += net_amount
    map[key].vat += vat_amount
  }
  return Object.values(map).sort((a, b) => b.rate - a.rate)
})
</script>

<template>
  <div class="space-y-2 text-sm">
    <div class="flex justify-between">
      <span class="text-gray-600">Summe Netto</span>
      <span class="font-medium">{{ formatCurrency(totals.net) }}</span>
    </div>

    <!-- VAT breakdown -->
    <template v-if="!kleinunternehmer">
      <div v-for="vb in vatBreakdown" :key="vb.rate" class="flex justify-between text-gray-500">
        <span>MwSt. {{ (vb.rate * 100).toFixed(0) }}% (auf {{ formatCurrency(vb.net) }})</span>
        <span>{{ formatCurrency(vb.vat) }}</span>
      </div>
    </template>
    <div v-else class="text-xs text-gray-400 italic">
      Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.
    </div>

    <hr class="border-gray-200" />

    <div class="flex justify-between text-base font-bold">
      <span>Gesamtbetrag</span>
      <span>{{ formatCurrency(totals.gross) }}</span>
    </div>

    <template v-if="paidAmount > 0">
      <div class="flex justify-between text-green-700">
        <span>Bereits bezahlt</span>
        <span>- {{ formatCurrency(paidAmount) }}</span>
      </div>
      <div class="flex justify-between font-bold text-primary-700">
        <span>Restbetrag</span>
        <span>{{ formatCurrency(remaining) }}</span>
      </div>
    </template>
  </div>
</template>
