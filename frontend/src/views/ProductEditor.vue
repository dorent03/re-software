<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProductsStore } from '@/store/products'
import FormInput from '@/components/FormInput.vue'

const route = useRoute()
const router = useRouter()
const store = useProductsStore()

const isEdit = computed(() => !!route.params.id)
const loading = ref(false)
const error = ref('')

const form = ref({
  name: '',
  article_number: '',
  description: '',
  unit: 'Stück',
  unit_price: 0,
  vat_rate: 0.19,
})

const vatOptions = [
  { value: 0.19, label: '19%' },
  { value: 0.07, label: '7%' },
  { value: 0, label: '0%' },
]

onMounted(async () => {
  if (isEdit.value) {
    await store.fetchProduct(route.params.id)
    if (store.currentProduct) {
      const p = store.currentProduct
      form.value = {
        name: p.name || '',
        article_number: p.article_number || '',
        description: p.description || '',
        unit: p.unit || 'Stück',
        unit_price: p.unit_price || 0,
        vat_rate: p.vat_rate ?? 0.19,
      }
    }
  }
})

async function handleSubmit() {
  error.value = ''
  if (!form.value.name) {
    error.value = 'Name ist erforderlich'
    return
  }
  if (form.value.unit_price < 0) {
    error.value = 'Preis muss positiv sein'
    return
  }
  loading.value = true
  try {
    if (isEdit.value) {
      await store.updateProduct(route.params.id, form.value)
    } else {
      await store.createProduct(form.value)
    }
    router.push('/products')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Speichern fehlgeschlagen'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl">
    <div class="mb-6">
      <button class="text-sm text-gray-500 hover:text-gray-700 mb-2" @click="router.push('/products')">
        &larr; Zurück zur Produktliste
      </button>
      <h2 class="text-xl font-bold text-gray-900">
        {{ isEdit ? 'Produkt bearbeiten' : 'Neues Produkt' }}
      </h2>
    </div>

    <div v-if="error" class="mb-4 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
      {{ error }}
    </div>

    <form class="card space-y-5" @submit.prevent="handleSubmit">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <FormInput v-model="form.name" label="Name" required placeholder="Produktname" />
        <FormInput v-model="form.article_number" label="Artikelnummer" placeholder="ART-001" />
      </div>

      <FormInput v-model="form.description" label="Beschreibung" type="textarea" placeholder="Produktbeschreibung..." />

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <FormInput v-model="form.unit_price" label="Einzelpreis (€)" type="number" required />
        <FormInput v-model="form.unit" label="Einheit" placeholder="Stück" />
        <div>
          <label class="label-text">MwSt.-Satz</label>
          <select v-model="form.vat_rate" class="input-field">
            <option v-for="opt in vatOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
      </div>

      <div class="flex gap-3 pt-2">
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? 'Speichern...' : 'Speichern' }}
        </button>
        <button type="button" class="btn-secondary" @click="router.push('/products')">
          Abbrechen
        </button>
      </div>
    </form>
  </div>
</template>
