<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const auth = useAuthStore()

const form = ref({
  email: '',
  password: '',
  confirmPassword: '',
  first_name: '',
  last_name: '',
  company_name: '',
  company_street: '',
  company_zip: '',
  company_city: '',
  company_country: 'DE',
})
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''

  if (
    !form.value.email ||
    !form.value.password ||
    !form.value.first_name ||
    !form.value.last_name ||
    !form.value.company_name ||
    !form.value.company_street ||
    !form.value.company_zip ||
    !form.value.company_city
  ) {
    error.value = 'Alle Pflichtfelder sind erforderlich'
    return
  }
  if (form.value.password.length < 8) {
    error.value = 'Passwort muss mindestens 8 Zeichen lang sein'
    return
  }
  if (form.value.password !== form.value.confirmPassword) {
    error.value = 'Passwörter stimmen nicht überein'
    return
  }

  loading.value = true
  try {
    const { confirmPassword, ...payload } = form.value
    await auth.register(payload)
    router.push('/login')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Registrierung fehlgeschlagen'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="w-full max-w-lg">
    <div class="card">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-900">Konto erstellen</h1>
        <p class="mt-2 text-sm text-gray-600">Registrieren Sie sich für RE-Software</p>
      </div>

      <form @submit.prevent="handleRegister" class="space-y-5">
        <div v-if="error" class="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {{ error }}
        </div>

        <!-- Persönliche Daten -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label for="first_name" class="label-text">Vorname <span class="text-red-500">*</span></label>
            <input id="first_name" v-model="form.first_name" type="text" class="input-field" placeholder="Max" />
          </div>
          <div>
            <label for="last_name" class="label-text">Nachname <span class="text-red-500">*</span></label>
            <input id="last_name" v-model="form.last_name" type="text" class="input-field" placeholder="Mustermann" />
          </div>
        </div>

        <div>
          <label for="reg_email" class="label-text">E-Mail <span class="text-red-500">*</span></label>
          <input id="reg_email" v-model="form.email" type="email" class="input-field" placeholder="name@firma.de" autocomplete="email" />
        </div>

        <!-- Firmendaten -->
        <div>
          <label for="company_name" class="label-text">Firmenname <span class="text-red-500">*</span></label>
          <input id="company_name" v-model="form.company_name" type="text" class="input-field" placeholder="Muster GmbH" />
        </div>

        <div>
          <label for="company_street" class="label-text">Straße <span class="text-red-500">*</span></label>
          <input id="company_street" v-model="form.company_street" type="text" class="input-field" placeholder="Musterstr. 1" />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label for="company_zip" class="label-text">PLZ <span class="text-red-500">*</span></label>
            <input id="company_zip" v-model="form.company_zip" type="text" class="input-field" placeholder="12345" />
          </div>
          <div>
            <label for="company_city" class="label-text">Stadt <span class="text-red-500">*</span></label>
            <input id="company_city" v-model="form.company_city" type="text" class="input-field" placeholder="Berlin" />
          </div>
        </div>

        <!-- Passwort -->
        <div>
          <label for="reg_password" class="label-text">Passwort <span class="text-red-500">*</span></label>
          <input id="reg_password" v-model="form.password" type="password" class="input-field" placeholder="Mindestens 8 Zeichen" autocomplete="new-password" />
        </div>

        <div>
          <label for="confirm_password" class="label-text">Passwort bestätigen <span class="text-red-500">*</span></label>
          <input id="confirm_password" v-model="form.confirmPassword" type="password" class="input-field" placeholder="Passwort wiederholen" autocomplete="new-password" />
        </div>

        <button type="submit" class="btn-primary w-full" :disabled="loading">
          <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {{ loading ? 'Registrieren...' : 'Registrieren' }}
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-gray-600">
        Bereits ein Konto?
        <router-link to="/login" class="font-medium text-primary-600 hover:text-primary-500">
          Jetzt anmelden
        </router-link>
      </p>
    </div>
  </div>
</template>
