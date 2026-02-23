import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')

  const isAuthenticated = computed(() => !!accessToken.value)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')

  /**
   * Login with email + password. Stores tokens and fetches user profile.
   * @param {string} loginEmail
   * @param {string} password
   */
  async function login(loginEmail, password) {
    const { data } = await api.post('/auth/login', {
      email: loginEmail,
      password,
    })
    accessToken.value = data.access_token
    refreshToken.value = data.refresh_token || ''
    localStorage.setItem('access_token', data.access_token)
    if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)

    await fetchUser()
  }

  /**
   * Register a new account.
   * @param {{ email: string, password: string, full_name: string, company_name: string }} payload
   */
  async function register(payload) {
    await api.post('/auth/register', payload)
  }

  /** Fetch the current user profile. */
  async function fetchUser() {
    try {
      const { data } = await api.get('/auth/me')
      user.value = data
    } catch {
      user.value = null
    }
  }

  /** Clear tokens and user state. */
  function logout() {
    accessToken.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  /** Restore session on page load. */
  async function init() {
    if (accessToken.value) {
      await fetchUser()
    }
  }

  return { user, accessToken, refreshToken, isAuthenticated, isAdmin, login, register, fetchUser, logout, init }
})
