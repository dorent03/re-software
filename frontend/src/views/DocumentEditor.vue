<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDocumentsStore } from '@/store/documents'
import { useCustomersStore } from '@/store/customers'
import { useProductsStore } from '@/store/products'
import { formatCurrency, statusBadgeClass, documentTypeLabel } from '@/utils/helpers'
import FormInput from '@/components/FormInput.vue'
import PositionTable from '@/components/PositionTable.vue'
import PaymentTable from '@/components/PaymentTable.vue'
import ReminderTable from '@/components/ReminderTable.vue'
import InvoiceTotals from '@/components/InvoiceTotals.vue'
import QRCodeDisplay from '@/components/QRCodeDisplay.vue'

const route = useRoute()
const router = useRouter()
const docStore = useDocumentsStore()
const customerStore = useCustomersStore()
const productStore = useProductsStore()

const isEdit = computed(() => !!route.params.id)
const loading = ref(false)
const error = ref('')
const activeTab = ref('details')

const DOC_TYPES = [
  { value: 'INVOICE', label: 'Rechnung' },
  { value: 'QUOTE', label: 'Angebot' },
  { value: 'DELIVERY_NOTE', label: 'Lieferschein' },
  { value: 'ORDER_CONFIRMATION', label: 'Auftragsbestätigung' },
  { value: 'PARTIAL_INVOICE', label: 'Abschlagsrechnung' },
  { value: 'CREDIT_NOTE', label: 'Gutschrift' },
  { value: 'CANCELLATION', label: 'Stornorechnung' },
]

const form = ref({
  document_type: 'INVOICE',
  customer_id: '',
  positions: [],
  notes: '',
  payment_terms_days: 14,
  service_date: '',
  related_document_id: '',
})

/** Related documents (parent + children) loaded from the API. */
const relatedDocs = ref({ parent: null, children: [] })

/** Partial invoice modal state. */
const showPartialModal = ref(false)
const partialForm = ref({ amount: 0, notes: '' })

/** Whether the document can be edited (only drafts). */
const canEdit = computed(() => {
  if (!isEdit.value) return true
  return docStore.currentDocument?.status === 'DRAFT'
})

const doc = computed(() => docStore.currentDocument)

/** Current IBAN / BIC etc. from company settings (stored in doc or fetched). */
const companyIban = computed(() => doc.value?.company_iban || '')
const companyBic = computed(() => doc.value?.company_bic || '')
const companyName = computed(() => doc.value?.company_name || '')

const isInvoiceType = computed(() => {
  const t = isEdit.value ? doc.value?.document_type : form.value.document_type
  return ['INVOICE', 'PARTIAL_INVOICE'].includes(t)
})

/** Whether the partial invoice button should be shown. */
const canCreatePartial = computed(() => {
  if (!isEdit.value || !doc.value) return false
  return (
    doc.value.document_type === 'INVOICE' &&
    !['CANCELLED', 'DRAFT'].includes(doc.value.status)
  )
})

/** Whether status can be changed to SENT. */
const canMarkSent = computed(() => {
  if (!isEdit.value || !doc.value) return false
  return doc.value.status === 'DRAFT'
})

/** Whether quote can be accepted/rejected. */
const canAcceptReject = computed(() => {
  if (!isEdit.value || !doc.value) return false
  return doc.value.document_type === 'QUOTE' && doc.value.status === 'SENT'
})

onMounted(async () => {
  customerStore.fetchCustomers({ limit: 500 })
  productStore.fetchProducts({ limit: 500 })
  docStore.fetchDocuments({ page: 1, limit: 100 })

  if (isEdit.value) {
    await docStore.fetchDocument(route.params.id)
    if (doc.value) {
      const existingItems = (doc.value.items || []).map((item) => ({
        product_id: item.product_id || '',
        name: item.name || '',
        description: item.description || '',
        quantity: item.quantity || 1,
        unit: item.unit || 'Stück',
        unit_price: item.unit_price || 0,
        vat_rate: item.vat_rate ?? 0.19,
        discount_percent: item.discount_percent || 0,
      }))
      form.value = {
        document_type: doc.value.document_type || 'INVOICE',
        customer_id: doc.value.customer_id || '',
        positions: existingItems,
        notes: doc.value.notes || '',
        payment_terms_days: doc.value.payment_terms_days ?? 14,
        service_date: doc.value.service_date || '',
        related_document_id: doc.value.related_document_id || '',
      }
    }
    // Load related documents
    loadRelatedDocuments()
  }
})

/** Fetch related (parent + children) documents from the API. */
async function loadRelatedDocuments() {
  try {
    relatedDocs.value = await docStore.fetchRelatedDocuments(route.params.id)
  } catch {
    relatedDocs.value = { parent: null, children: [] }
  }
}

async function handleSave() {
  error.value = ''
  if (!form.value.customer_id) {
    error.value = 'Bitte wählen Sie einen Kunden aus'
    return
  }
  if (form.value.positions.length === 0) {
    error.value = 'Mindestens eine Position ist erforderlich'
    return
  }
  for (const pos of form.value.positions) {
    if (!(pos.name || pos.description)) {
      error.value = 'Jede Position benötigt einen Namen oder eine Beschreibung'
      return
    }
    if (!(Number(pos.quantity) > 0)) {
      error.value = 'Jede Position benötigt eine Menge größer 0'
      return
    }
    if (!(Number(pos.unit_price) > 0)) {
      error.value = 'Jede Position benötigt einen Einzelpreis größer 0'
      return
    }
  }

  loading.value = true
  try {
    const items = form.value.positions.map((pos) => ({
      product_id: pos.product_id,
      quantity: pos.quantity,
      discount_percent: pos.discount_percent || 0,
      name: pos.name || pos.description || '',
      description: pos.description || '',
      unit: pos.unit,
      unit_price: pos.unit_price,
      vat_rate: pos.vat_rate,
    }))

    const payload = {
      document_type: form.value.document_type,
      customer_id: form.value.customer_id,
      items,
      notes: form.value.notes || '',
      payment_terms_days: form.value.payment_terms_days || 14,
      service_date: form.value.service_date || undefined,
      related_document_id: form.value.related_document_id || undefined,
    }

    if (isEdit.value) {
      await docStore.updateDocument(route.params.id, payload)
      await docStore.fetchDocument(route.params.id)
    } else {
      const created = await docStore.createDocument(payload)
      router.push(`/documents/${created.id}`)
    }
  } catch (err) {
    const detail = err.response?.data?.detail
    error.value = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail[0]?.msg || JSON.stringify(detail) : 'Speichern fehlgeschlagen'
  } finally {
    loading.value = false
  }
}

async function handleAddPayment(payment) {
  try {
    await docStore.addPayment(route.params.id, payment)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Zahlung fehlgeschlagen'
  }
}

async function handleAddReminder(reminder) {
  try {
    await docStore.addReminder(route.params.id, reminder)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Mahnung fehlgeschlagen'
  }
}

async function handleCancel() {
  if (!confirm('Dokument wirklich stornieren? Dies erstellt eine Stornorechnung.')) return
  try {
    const cancellation = await docStore.cancelDocument(route.params.id)
    router.push(`/documents/${cancellation.id}`)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Stornierung fehlgeschlagen'
  }
}

async function handleCreditNote() {
  if (!confirm('Gutschrift erstellen?')) return
  try {
    const credit = await docStore.createCreditNote(route.params.id)
    router.push(`/documents/${credit.id}`)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Gutschrift fehlgeschlagen'
  }
}

async function handleConvert() {
  if (!confirm('Angebot in Rechnung umwandeln?')) return
  try {
    const invoice = await docStore.convertToInvoice(route.params.id)
    router.push(`/documents/${invoice.id}`)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Umwandlung fehlgeschlagen'
  }
}

async function handleDownloadPdf() {
  try {
    const url = await docStore.downloadPdf(route.params.id)
    window.open(url, '_blank')
  } catch (err) {
    error.value = err.response?.data?.detail || 'PDF-Download fehlgeschlagen'
  }
}

async function handleXRechnung() {
  try {
    const url = await docStore.getXRechnung(route.params.id)
    const a = document.createElement('a')
    a.href = url
    a.download = `${doc.value?.document_number || 'xrechnung'}.xml`
    a.click()
  } catch (err) {
    error.value = err.response?.data?.detail || 'XRechnung fehlgeschlagen'
  }
}

async function handleZugferd() {
  try {
    const url = await docStore.getZugferd(route.params.id)
    const a = document.createElement('a')
    a.href = url
    a.download = `${doc.value?.document_number || 'zugferd'}.pdf`
    a.click()
  } catch (err) {
    error.value = err.response?.data?.detail || 'ZUGFeRD fehlgeschlagen'
  }
}

/** Change document status (DRAFT -> SENT, etc.). */
async function handleStatusChange(newStatus) {
  try {
    await docStore.updateStatus(route.params.id, newStatus)
    await docStore.fetchDocument(route.params.id)
    loadRelatedDocuments()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Statuswechsel fehlgeschlagen'
  }
}

/** Mark quote as accepted. */
async function handleAcceptQuote() {
  await handleStatusChange('ACCEPTED')
}

/** Mark quote as rejected. */
async function handleRejectQuote() {
  if (!confirm('Angebot wirklich ablehnen?')) return
  await handleStatusChange('REJECTED')
}

/** Mark document as sent. */
async function handleMarkSent() {
  await handleStatusChange('SENT')
}

/** Open partial invoice modal. */
function openPartialModal() {
  partialForm.value = { amount: 0, notes: '' }
  showPartialModal.value = true
}

/** Submit partial invoice creation. */
async function handleCreatePartial() {
  if (partialForm.value.amount <= 0) {
    error.value = 'Betrag muss positiv sein'
    return
  }
  try {
    const partial = await docStore.createPartialInvoice(route.params.id, {
      amount: partialForm.value.amount,
      notes: partialForm.value.notes,
    })
    showPartialModal.value = false
    router.push(`/documents/${partial.id}`)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Abschlagsrechnung fehlgeschlagen'
  }
}

/** Quick add product to positions. */
function addProductToPositions(productId) {
  const prod = productStore.products.find((p) => p.id === productId)
  if (!prod) return
  form.value.positions = [
    ...form.value.positions,
    {
      product_id: prod.id,
      name: prod.name,
      description: prod.description || '',
      quantity: 1,
      unit: prod.unit || 'Stück',
      unit_price: prod.unit_price || 0,
      vat_rate: prod.vat_rate ?? 0.19,
      discount_percent: 0,
    },
  ]
}

const baseTabs = [
  { key: 'details', label: 'Details' },
  { key: 'positions', label: 'Positionen' },
  { key: 'payments', label: 'Zahlungen' },
  { key: 'reminders', label: 'Mahnungen' },
]

const tabs = computed(() => {
  if (isEdit.value && doc.value?.document_type === 'QUOTE') {
    return [...baseTabs, { key: 'order-confirmation', label: 'Auftragsbestätigung' }]
  }
  return baseTabs
})

/** Order confirmation created from this quote (from related documents). */
const orderConfirmation = computed(() => {
  const children = relatedDocs.value?.children || []
  return children.find((d) => d.document_type === 'ORDER_CONFIRMATION') || null
})
</script>

<template>
  <div>
    <!-- Back + Title -->
    <div class="mb-6">
      <button class="text-sm text-gray-500 hover:text-gray-700 mb-2" @click="router.push('/documents')">
        &larr; Zurück zur Dokumentliste
      </button>
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 class="text-xl font-bold text-gray-900">
            <template v-if="isEdit && doc">
              {{ documentTypeLabel(doc.document_type) }} {{ doc.document_number }}
            </template>
            <template v-else>Neues Dokument</template>
          </h2>
          <div v-if="isEdit && doc" class="flex items-center gap-2 mt-1">
            <span :class="['badge', statusBadgeClass(doc.status)]">{{ doc.status }}</span>
            <span v-if="doc.customer_name" class="text-sm text-gray-500">{{ doc.customer_name }}</span>
          </div>
        </div>

        <!-- Action buttons -->
        <div v-if="isEdit && doc" class="flex flex-wrap gap-2">
          <!-- Status changes -->
          <button v-if="canMarkSent" class="btn-primary btn-sm" @click="handleMarkSent">
            Als gesendet markieren
          </button>
          <button v-if="canAcceptReject" class="btn-primary btn-sm" @click="handleAcceptQuote">
            Akzeptieren
          </button>
          <button v-if="canAcceptReject" class="btn-danger btn-sm" @click="handleRejectQuote">
            Ablehnen
          </button>

          <!-- PDF / Export -->
          <button class="btn-secondary btn-sm" @click="handleDownloadPdf">PDF</button>
          <router-link :to="`/documents/${route.params.id}/pdf`" class="btn-secondary btn-sm">Vorschau</router-link>
          <button v-if="isInvoiceType" class="btn-secondary btn-sm" @click="handleXRechnung">XRechnung</button>
          <button v-if="isInvoiceType" class="btn-secondary btn-sm" @click="handleZugferd">ZUGFeRD</button>

          <!-- Conversions -->
          <button v-if="doc.document_type === 'QUOTE' && doc.status === 'ACCEPTED'" class="btn-primary btn-sm" @click="handleConvert">
            In Rechnung umwandeln
          </button>
          <button v-if="canCreatePartial" class="btn-secondary btn-sm" @click="openPartialModal">
            Abschlagsrechnung
          </button>
          <button
            v-if="['SENT', 'PAID', 'PARTIALLY_PAID', 'OVERDUE'].includes(doc.status) && isInvoiceType"
            class="btn-danger btn-sm"
            @click="handleCancel"
          >
            Stornieren
          </button>
          <button
            v-if="doc.status === 'PAID' && isInvoiceType"
            class="btn-secondary btn-sm"
            @click="handleCreditNote"
          >
            Gutschrift
          </button>
        </div>
      </div>
    </div>

    <div v-if="error" class="mb-4 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
      {{ error }}
    </div>

    <!-- Tabs -->
    <div class="border-b border-gray-200 mb-6">
      <nav class="flex gap-6">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="[
            'py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === tab.key
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700',
          ]"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </nav>
    </div>

    <!-- TAB: Details -->
    <div v-show="activeTab === 'details'" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 card space-y-5">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="label-text">Dokumenttyp</label>
            <select
              v-model="form.document_type"
              class="input-field"
              :disabled="isEdit"
            >
              <option v-for="t in DOC_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
          </div>
          <div>
            <label class="label-text">Kunde <span class="text-red-500">*</span></label>
            <select v-model="form.customer_id" class="input-field" :disabled="!canEdit">
              <option value="" disabled>Kunde wählen</option>
              <option
                v-for="c in customerStore.customers"
                :key="c.id"
                :value="c.id"
              >
                {{ c.name }}
              </option>
            </select>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <FormInput
            v-model="form.payment_terms_days"
            label="Zahlungsziel (Tage)"
            type="number"
            :disabled="!canEdit"
          />
          <FormInput
            v-model="form.service_date"
            label="Leistungsdatum"
            type="date"
            :disabled="!canEdit"
          />
          <div>
            <label class="label-text">Bezugsdokument</label>
            <select v-model="form.related_document_id" class="input-field" :disabled="!canEdit">
              <option value="">Kein Bezug</option>
              <option
                v-for="d in docStore.documents"
                :key="d.id"
                :value="d.id"
              >
                {{ d.document_number }} ({{ documentTypeLabel(d.document_type) }})
              </option>
            </select>
          </div>
        </div>

        <FormInput
          v-model="form.notes"
          label="Notizen"
          type="textarea"
          placeholder="Interne Notizen oder Hinweistext..."
          :disabled="!canEdit"
        />

        <div v-if="canEdit" class="flex gap-3 pt-2">
          <button class="btn-primary" :disabled="loading" @click="handleSave">
            {{ loading ? 'Speichern...' : 'Speichern' }}
          </button>
          <button class="btn-secondary" @click="router.push('/documents')">Abbrechen</button>
        </div>
      </div>

      <!-- Right sidebar: Totals + QR -->
      <div class="space-y-6">
        <div class="card">
          <h3 class="text-sm font-semibold text-gray-700 mb-3">Beträge</h3>
          <InvoiceTotals
            :positions="form.positions"
            :paid-amount="doc?.totals?.paid_amount || 0"
          />
        </div>

        <div v-if="isEdit && isInvoiceType && companyIban" class="card">
          <QRCodeDisplay
            :iban="companyIban"
            :bic="companyBic"
            :recipient="companyName"
            :amount="doc?.totals?.remaining_amount ?? doc?.totals?.gross ?? 0"
            :reference="doc?.document_number || ''"
          />
        </div>

        <!-- Related Documents -->
        <div v-if="isEdit && (relatedDocs.parent || relatedDocs.children.length > 0)" class="card">
          <h3 class="text-sm font-semibold text-gray-700 mb-3">Verknüpfte Dokumente</h3>

          <div v-if="relatedDocs.parent" class="mb-3">
            <span class="text-xs text-gray-500 uppercase font-semibold">Bezugsdokument</span>
            <router-link
              :to="`/documents/${relatedDocs.parent.id}`"
              class="block mt-1 p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <span class="font-medium text-primary-600">{{ relatedDocs.parent.document_number }}</span>
              <span class="text-xs text-gray-500 ml-2">{{ documentTypeLabel(relatedDocs.parent.document_type) }}</span>
              <span :class="['badge ml-2', statusBadgeClass(relatedDocs.parent.status)]">{{ relatedDocs.parent.status }}</span>
              <span class="block text-sm text-gray-600 mt-1">{{ formatCurrency(relatedDocs.parent.gross) }}</span>
            </router-link>
          </div>

          <div v-if="relatedDocs.children.length > 0">
            <span class="text-xs text-gray-500 uppercase font-semibold">Abgeleitete Dokumente</span>
            <div class="mt-1 space-y-1">
              <router-link
                v-for="child in relatedDocs.children"
                :key="child.id"
                :to="`/documents/${child.id}`"
                class="block p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <span class="font-medium text-primary-600">{{ child.document_number }}</span>
                <span class="text-xs text-gray-500 ml-2">{{ documentTypeLabel(child.document_type) }}</span>
                <span :class="['badge ml-2', statusBadgeClass(child.status)]">{{ child.status }}</span>
                <span class="block text-sm text-gray-600 mt-1">{{ formatCurrency(child.gross) }}</span>
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB: Positions -->
    <div v-show="activeTab === 'positions'" class="card">
      <!-- Quick product insert -->
      <div v-if="canEdit" class="mb-4">
        <label class="label-text">Produkt hinzufügen</label>
        <select
          class="input-field max-w-xs"
          @change="addProductToPositions($event.target.value); $event.target.value = ''"
        >
          <option value="">Produkt wählen...</option>
          <option v-for="p in productStore.products" :key="p.id" :value="p.id">
            {{ p.article_number ? p.article_number + ' — ' : '' }}{{ p.name }} ({{ formatCurrency(p.unit_price) }})
          </option>
        </select>
      </div>

      <PositionTable
        v-model:positions="form.positions"
        :editable="canEdit"
      />

      <div v-if="canEdit" class="mt-4">
        <button class="btn-primary" :disabled="loading" @click="handleSave">Speichern</button>
      </div>
    </div>

    <!-- TAB: Payments -->
    <div v-show="activeTab === 'payments'" class="card">
      <PaymentTable
        :payments="doc?.payments || []"
        :editable="isEdit && isInvoiceType && !['PAID', 'CANCELLED'].includes(doc?.status)"
        @add-payment="handleAddPayment"
      />
    </div>

    <!-- TAB: Reminders -->
    <div v-show="activeTab === 'reminders'" class="card">
      <ReminderTable
        :reminders="doc?.reminders || []"
        :editable="isEdit && isInvoiceType && ['SENT', 'OVERDUE', 'PARTIALLY_PAID'].includes(doc?.status)"
        @add-reminder="handleAddReminder"
      />
    </div>

    <!-- TAB: Auftragsbestätigung (nur bei Angebot) -->
    <div v-show="activeTab === 'order-confirmation'" class="card">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Auftragsbestätigung</h3>
      <p v-if="!orderConfirmation" class="text-sm text-gray-500">
        Wird automatisch erstellt, sobald das Angebot akzeptiert wird.
      </p>
      <div v-else class="rounded-lg border border-gray-200 bg-gray-50 p-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <span class="font-medium text-gray-900">{{ orderConfirmation.document_number }}</span>
            <span :class="['badge ml-2', statusBadgeClass(orderConfirmation.status)]">
              {{ orderConfirmation.status }}
            </span>
            <span class="block text-sm text-gray-600 mt-1">
              {{ formatCurrency(orderConfirmation.gross) }}
            </span>
          </div>
          <router-link
            :to="`/documents/${orderConfirmation.id}`"
            class="btn-primary btn-sm"
          >
            Auftragsbestätigung öffnen
          </router-link>
        </div>
      </div>
    </div>

    <!-- Partial Invoice Modal -->
    <div v-if="showPartialModal" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0 bg-black/40" @click="showPartialModal = false" />
      <div class="relative bg-white rounded-xl shadow-xl p-6 w-full max-w-md mx-4 z-10">
        <h3 class="text-lg font-bold text-gray-900 mb-4">Abschlagsrechnung erstellen</h3>
        <p class="text-sm text-gray-500 mb-4">
          Erstellt eine Teilrechnung zum Dokument {{ doc?.document_number }}.
          Gesamtbetrag: {{ formatCurrency(doc?.totals?.gross) }}
        </p>
        <div class="space-y-4">
          <div>
            <label class="label-text">Betrag (brutto) <span class="text-red-500">*</span></label>
            <input
              v-model.number="partialForm.amount"
              type="number"
              step="0.01"
              min="0.01"
              class="input-field"
              placeholder="z.B. 500.00"
            />
          </div>
          <div>
            <label class="label-text">Notizen</label>
            <textarea v-model="partialForm.notes" class="input-field" rows="2" placeholder="Optional" />
          </div>
        </div>
        <div class="flex gap-3 mt-6">
          <button class="btn-primary" @click="handleCreatePartial">Erstellen</button>
          <button class="btn-secondary" @click="showPartialModal = false">Abbrechen</button>
        </div>
      </div>
    </div>
  </div>
</template>
