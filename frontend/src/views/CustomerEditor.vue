<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCustomersStore } from '@/store/customers'
import FormInput from '@/components/FormInput.vue'

const route = useRoute()
const router = useRouter()
const store = useCustomersStore()

const isEdit = computed(() => !!route.params.id)
const loading = ref(false)
const error = ref('')

const form = ref({
  name: '',
  email: '',
  phone: '',
  street: '',
  zip_code: '',
  city: '',
  country: 'DE',
  tax_id: '',
  notes: '',
})

onMounted(async () => {
  if (isEdit.value) {
    await store.fetchCustomer(route.params.id)
    if (store.currentCustomer) {
      const c = store.currentCustomer
      form.value = {
        name: c.name || '',
        email: c.email || '',
        phone: c.phone || '',
        street: c.street || '',
        zip_code: c.zip_code || '',
        city: c.city || '',
        country: (c.country || 'DE').slice(0, 5),
        tax_id: c.tax_id || '',
        notes: c.notes || '',
      }
    }
  }
})

function getApiErrorMessage(err) {
  if (err instanceof Error) return err.message || 'Speichern fehlgeschlagen'
  return 'Speichern fehlgeschlagen'
}

async function handleSubmit() {
  error.value = ''

  const name = String(form.value.name || '').trim()
  const street = String(form.value.street || '').trim()
  const zipCode = String(form.value.zip_code || '').trim()
  const city = String(form.value.city || '').trim()

  if (!name) {
    error.value = 'Name ist erforderlich'
    return
  }
  if (!street) {
    error.value = 'Straße ist erforderlich'
    return
  }
  if (!zipCode) {
    error.value = 'PLZ ist erforderlich'
    return
  }
  if (!city) {
    error.value = 'Stadt ist erforderlich'
    return
  }

  loading.value = true
  try {
    const payload = {
      name,
      street,
      zip_code: zipCode,
      city,
      country: (form.value.country || 'DE').slice(0, 5),
      email: (form.value.email || '').trim() || undefined,
      phone: (form.value.phone || '').trim() || undefined,
      tax_id: (form.value.tax_id || '').trim() || undefined,
      notes: (form.value.notes || '').trim() || undefined,
    }
    if (isEdit.value) {
      await store.updateCustomer(route.params.id, payload)
    } else {
      await store.createCustomer(payload)
    }
    router.push('/customers')
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl">
    <div class="mb-6">
      <button class="text-sm text-gray-500 hover:text-gray-700 mb-2" @click="router.push('/customers')">
        &larr; Zurück zur Kundenliste
      </button>
      <h2 class="text-xl font-bold text-gray-900">
        {{ isEdit ? 'Kunde bearbeiten' : 'Neuer Kunde' }}
      </h2>
    </div>

    <div v-if="error" class="mb-4 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
      {{ error }}
    </div>

    <form class="card space-y-5" @submit.prevent="handleSubmit">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <FormInput v-model="form.name" label="Name" required placeholder="Firma / Name" />
        <FormInput v-model="form.email" label="E-Mail" type="email" placeholder="kunde@firma.de" />
        <FormInput v-model="form.phone" label="Telefon" placeholder="+49 123 456789" />
        <FormInput v-model="form.tax_id" label="USt-IdNr." placeholder="DE123456789" />
      </div>

      <hr class="border-gray-200" />

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="sm:col-span-2">
          <FormInput v-model="form.street" label="Straße" placeholder="Musterstr. 1" />
        </div>
        <FormInput v-model="form.zip_code" label="PLZ" placeholder="12345" />
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <FormInput v-model="form.city" label="Stadt" placeholder="Berlin" />
        <FormInput v-model="form.country" label="Land (z. B. DE)" placeholder="DE" />
      </div>

      <FormInput v-model="form.notes" label="Notizen" type="textarea" placeholder="Interne Notizen..." />

      <div class="flex gap-3 pt-2">
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? 'Speichern...' : 'Speichern' }}
        </button>
        <button type="button" class="btn-secondary" @click="router.push('/customers')">
          Abbrechen
        </button>
      </div>
    </form>
  </div>
</template>
