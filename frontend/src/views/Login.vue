<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  if (!email.value || !password.value) {
    error.value = 'E-Mail und Passwort sind erforderlich'
    return
  }
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Anmeldung fehlgeschlagen'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="w-full max-w-md">
    <div class="card">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-900">RE-Software</h1>
        <p class="mt-2 text-sm text-gray-600">Melden Sie sich an, um fortzufahren</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-5">
        <div v-if="error" class="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {{ error }}
        </div>

        <div>
          <label for="email" class="label-text">E-Mail</label>
          <input
            id="email"
            v-model="email"
            type="email"
            class="input-field"
            placeholder="name@firma.de"
            autocomplete="email"
          />
        </div>

        <div>
          <label for="password" class="label-text">Passwort</label>
          <input
            id="password"
            v-model="password"
            type="password"
            class="input-field"
            placeholder="••••••••"
            autocomplete="current-password"
          />
        </div>

        <button type="submit" class="btn-primary w-full" :disabled="loading">
          <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {{ loading ? 'Anmelden...' : 'Anmelden' }}
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-gray-600">
        Noch kein Konto?
        <router-link to="/register" class="font-medium text-primary-600 hover:text-primary-500">
          Jetzt registrieren
        </router-link>
      </p>
    </div>
  </div>
</template>
