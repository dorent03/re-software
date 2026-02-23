<script setup>
import { computed } from 'vue'
import QrcodeVue from 'qrcode.vue'

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
    (props.recipient || '').slice(0, 70),
    props.iban.replace(/\s/g, ''),
    `EUR${props.amount.toFixed(2)}`,
    '',
    (props.reference || '').slice(0, 140),
    '',
    '',
  ]
  return lines.join('\n')
})
</script>

<template>
  <div v-if="epcPayload" class="flex flex-col items-center gap-2">
    <div class="rounded-lg border border-gray-200 bg-white p-3">
      <QrcodeVue :value="epcPayload" :size="176" level="M" render-as="svg" />
    </div>
    <p class="text-xs text-gray-500 text-center max-w-[200px]">
      SEPA-Überweisung<br />
      {{ reference }}
    </p>
  </div>
</template>
