import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

/** Attach JWT token from localStorage to every request. */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/**
 * Handle 401 responses globally.
 * Only clear tokens and redirect when the /auth/me probe fails (confirms
 * the token is truly invalid), not on every background 401.
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const url = error.config?.url || ''
      const isAuthCheck = url.includes('/auth/me')

      if (isAuthCheck) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  },
)

export default api
