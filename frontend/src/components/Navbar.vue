<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const pageTitle = computed(() => route.meta.title || 'RE-Software')
const userName = computed(() => {
  if (auth.user?.first_name) return `${auth.user.first_name} ${auth.user.last_name || ''}`.trim()
  return auth.user?.email || ''
})

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <header class="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4 md:px-6">
    <!-- Page title -->
    <h1 class="text-lg font-semibold text-gray-800 truncate ml-10 lg:ml-0">
      {{ pageTitle }}
    </h1>

    <!-- Right side: user + logout -->
    <div class="flex items-center gap-4">
      <span class="hidden sm:block text-sm text-gray-600">{{ userName }}</span>
      <button
        class="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
        @click="logout"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
        </svg>
        Abmelden
      </button>
    </div>
  </header>
</template>
