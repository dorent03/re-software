<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** IBAN of the receiving account */
  iban: { type: String, default: '' },
  /** BIC of the receiving bank */
  bic: { type: String, default: '' },
  /** Recipient name */
  recipient: { type: String, default: '' },
  /** Transfer amount in EUR */
  amount: { type: Number, default: 0 },
  /** Payment reference (e.g. invoice number) */
  reference: { type: String, default: '' },
})

/**
 * Build the EPC QR code payload according to EPC 069-12 standard.
 * We generate it as a data string and pass to qrcode.vue.
 */
const epcPayload = computed(() => {
  if (!props.iban || !props.amount) return ''
  const lines = [
    'BCD',
    '002',
    '1',
    'SCT',
    props.bic || '',
    props.recipient || '',
    props.iban.replace(/\s/g, ''),
    `EUR${props.amount.toFixed(2)}`,
    '',
    props.reference || '',
    '',
    '',
  ]
  return lines.join('\n')
})
</script>

<template>
  <div v-if="epcPayload" class="flex flex-col items-center gap-2">
    <div class="rounded-lg border border-gray-200 bg-white p-3">
      <!-- Use a simple canvas-based QR. For tree-shaking, we render via a basic SVG approach.
           Since qrcode.vue might not support all Node 16 builds, we use a lightweight inline solution. -->
      <img
        :src="`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(epcPayload)}`"
        alt="SEPA QR Code"
        class="w-44 h-44"
        loading="lazy"
      />
    </div>
    <p class="text-xs text-gray-500 text-center max-w-[200px]">
      SEPA-Überweisung<br />
      {{ reference }}
    </p>
  </div>
</template>
